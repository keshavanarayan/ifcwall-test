import uuid
import time
import tempfile
import ifcopenshell
import helperfunctions as hf

O = 0., 0., 0.
X = 1., 0., 0.
Y = 0., 1., 0.
Z = 0., 0., 1.


def ifcconvert(axispoints, basepoints, h, f, write):
       
    create_guid = lambda: ifcopenshell.guid.compress(uuid.uuid1().hex)

    # IFC template creation

    #filename = "hello.ifc"
    filename = f
    timestamp = time.time()
    timestring = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(timestamp))
    creator = "Keshava Narayan"
    organization = "KGA"
    application, application_version = "IfcOpenShell", "0.5"
    project_globalid, project_name = create_guid(), "Hello Wall"
        
    # A template IFC file to quickly populate entity instances for an IfcProject with its dependencies
    template = """ISO-10303-21;
    HEADER;
    FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');
    FILE_NAME('%(filename)s','%(timestring)s',('%(creator)s'),('%(organization)s'),'%(application)s','%(application)s','');
    FILE_SCHEMA(('IFC2X3'));
    ENDSEC;
    DATA;
    #1=IFCPERSON($,$,'%(creator)s',$,$,$,$,$);
    #2=IFCORGANIZATION($,'%(organization)s',$,$,$);
    #3=IFCPERSONANDORGANIZATION(#1,#2,$);
    #4=IFCAPPLICATION(#2,'%(application_version)s','%(application)s','');
    #5=IFCOWNERHISTORY(#3,#4,$,.ADDED.,$,#3,#4,%(timestamp)s);
    #6=IFCDIRECTION((1.,0.,0.));
    #7=IFCDIRECTION((0.,0.,1.));
    #8=IFCCARTESIANPOINT((0.,0.,0.));
    #9=IFCAXIS2PLACEMENT3D(#8,#7,#6);
    #10=IFCDIRECTION((0.,1.,0.));
    #11=IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,1.E-05,#9,#10);
    #12=IFCDIMENSIONALEXPONENTS(0,0,0,0,0,0,0);
    #13=IFCSIUNIT(*,.LENGTHUNIT.,$,.METRE.);
    #14=IFCSIUNIT(*,.AREAUNIT.,$,.SQUARE_METRE.);
    #15=IFCSIUNIT(*,.VOLUMEUNIT.,$,.CUBIC_METRE.);
    #16=IFCSIUNIT(*,.PLANEANGLEUNIT.,$,.RADIAN.);
    #17=IFCMEASUREWITHUNIT(IFCPLANEANGLEMEASURE(0.017453292519943295),#16);
    #18=IFCCONVERSIONBASEDUNIT(#12,.PLANEANGLEUNIT.,'DEGREE',#17);
    #19=IFCUNITASSIGNMENT((#13,#14,#15,#18));
    #20=IFCPROJECT('%(project_globalid)s',#5,'%(project_name)s',$,$,$,$,(#11),#19);
    ENDSEC;
    END-ISO-10303-21;
    """ % locals()

    # Write the template to a temporary file 
    temp_handle, temp_filename = tempfile.mkstemp(suffix=".ifc")
    with open(temp_filename, "w") as f:
        f.write(template)
    
    # Obtain references to instances defined in template
    ifcfile = ifcopenshell.open(temp_filename)
    owner_history = ifcfile.by_type("IfcOwnerHistory")[0]
    project = ifcfile.by_type("IfcProject")[0]
    context = ifcfile.by_type("IfcGeometricRepresentationContext")[0]

    # IFC hierarchy creation
    site_placement = hf.create_ifclocalplacement(ifcfile)
    site = ifcfile.createIfcSite(create_guid(), owner_history, "Site", None, None, site_placement, None, None, "ELEMENT", None, None, None, None, None)

    building_placement = hf.create_ifclocalplacement(ifcfile, relative_to=site_placement)
    building = ifcfile.createIfcBuilding(create_guid(), owner_history, 'Building', None, None, building_placement, None, None, "ELEMENT", None, None, None)

    storey_placement = hf.create_ifclocalplacement(ifcfile, relative_to=building_placement)
    elevation = 0.0
    building_storey = ifcfile.createIfcBuildingStorey(create_guid(), owner_history, 'Storey', None, None, storey_placement, None, None, "ELEMENT", elevation)

    container_storey = ifcfile.createIfcRelAggregates(create_guid(), owner_history, "Building Container", None, building, [building_storey])
    container_site = ifcfile.createIfcRelAggregates(create_guid(), owner_history, "Site Container", None, site, [building])
    container_project = ifcfile.createIfcRelAggregates(create_guid(), owner_history, "Project Container", None, project, [site])


    # Wall creation: Define the wall shape as a polyline axis and an extruded area solid
    wall_placement = hf.create_ifclocalplacement(ifcfile, relative_to=storey_placement)
    polyline = hf.create_ifcpolyline(ifcfile, axispoints)
    axis_representation = ifcfile.createIfcShapeRepresentation(context, "Axis", "Curve2D", [polyline])

    extrusion_placement = hf.create_ifcaxis2placement(ifcfile, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0))

    
    point_list_extrusion_area = basepoints
    solid = hf.create_ifcextrudedareasolid(ifcfile, point_list_extrusion_area, extrusion_placement, (0.0, 0.0, 1.0), h)
    body_representation = ifcfile.createIfcShapeRepresentation(context, "Body", "SweptSolid", [solid])

    product_shape = ifcfile.createIfcProductDefinitionShape(None, None, [axis_representation, body_representation])

    wall = ifcfile.createIfcWallStandardCase(create_guid(), owner_history, "Wall", "An awesome wall", None, wall_placement, product_shape, None)

    # Define and associate the wall material
    material = ifcfile.createIfcMaterial("wall material")
    material_layer = ifcfile.createIfcMaterialLayer(material, 0.2, None)
    material_layer_set = ifcfile.createIfcMaterialLayerSet([material_layer], None)
    material_layer_set_usage = ifcfile.createIfcMaterialLayerSetUsage(material_layer_set, "AXIS2", "POSITIVE", -0.1)
    ifcfile.createIfcRelAssociatesMaterial(create_guid(), owner_history, RelatedObjects=[wall], RelatingMaterial=material_layer_set_usage)



    # Write the contents of the file to disk
    if(write == True):
        ifcfile.write(filename)
        return "File Exported"
        #return axispoints


if __name__ == "__main__":
    axispoints = [(0.0, 0.0, 0.0),(0.0, 0.37, 0.0) ]
    basepoints = [(0.0, 0.37, 0.0), (0.0, 0.0, 0.0), (0.07, 0.0, 0.0), (0.07, 0.37, 0.0), (0.0, 0.37, 0.0)]
    h=3
    f = "Keshav.ifc"
    write = True

    ifcconvert(axispoints, basepoints, h, f, write)
# BlenderBIM Add-on - OpenBIM Blender Add-on
# Copyright (C) 2021 Dion Moult <dion@thinkmoult.com>
#
# This file is part of BlenderBIM Add-on.
#
# BlenderBIM Add-on is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# BlenderBIM Add-on is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with BlenderBIM Add-on.  If not, see <http://www.gnu.org/licenses/>.


# This can be packaged with `pyinstaller --onefile --hidden-import numpy --collect-all ifcopenshell --clean obj2ifc.py`
import pywavefront
import ifcopenshell
import ifcopenshell.api
import ifcopenshell.api.owner.settings
from pathlib import Path



path = "wallmesh.obj"

basename = Path(path).stem




file = ifcopenshell.api.run("project.create_file", version="IFC2X3")
person = ifcopenshell.api.run("owner.add_person", file)
person.Id = person.GivenName = None
person.FamilyName = "user"
org = ifcopenshell.api.run("owner.add_organisation", file)
org.Id = None
org.Name = "template"
user = ifcopenshell.api.run("owner.add_person_and_organisation", file, person=person, organisation=org)
application = ifcopenshell.api.run("owner.add_application", file)
ifcopenshell.api.owner.settings.get_user = lambda ifc: user
ifcopenshell.api.owner.settings.get_application = lambda ifc: application

project = ifcopenshell.api.run("root.create_entity", file, ifc_class="IfcProject", name=basename)
#project = file.by_type("IfcProject")[0]



lengthunit = ifcopenshell.api.run("unit.add_si_unit", file, unit_type="LENGTHUNIT", name="METRE")
ifcopenshell.api.run("unit.assign_unit", file, units=[lengthunit])
model = ifcopenshell.api.run("context.add_context", file, context_type="Model")

context = ifcopenshell.api.run(
    "context.add_context",
    file,
    context_type="Model",
    context_identifier="Body",
    target_view="MODEL_VIEW",
    parent=model,
)
#context = file.by_type("IfcGeometricRepresentationContext")[0]

site = ifcopenshell.api.run("root.create_entity", file, ifc_class="IfcSite", name="My Site")
building = ifcopenshell.api.run("root.create_entity", file, ifc_class="IfcBuilding", name="My Building")
storey = ifcopenshell.api.run(
    "root.create_entity", file, ifc_class="IfcBuildingStorey", name="My Storey"
)
ifcopenshell.api.run("aggregate.assign_object", file, product=site, relating_object=project)
ifcopenshell.api.run("aggregate.assign_object", file, product=building, relating_object=site)
ifcopenshell.api.run("aggregate.assign_object", file, product=storey, relating_object=building)

origin = file.createIfcAxis2Placement3D(
    file.createIfcCartesianPoint((0.0, 0.0, 0.0)),
    file.createIfcDirection((0.0, 0.0, 1.0)),
    file.createIfcDirection((1.0, 0.0, 0.0)),
)
placement = file.createIfcLocalPlacement(None, origin)
history = ifcopenshell.api.run("owner.create_owner_history", file)



#scene = pywavefront.Wavefront(path, create_materials=True, collect_faces=True)

vertices = [(0.00032, 0.00032, 0.07385), (0.07385, 0.00032, 0.00032), (0.00032, 0.00032, 0.00032), (0.07385, 0.07385, 0.00032), (0.07385, 0.07385, 0.07385), (0.07385, 0.07385, 0.00032), (0.00032, 0.07385, 0.00032), (0.07385, 0.07385, 0.00032), (-0.00388, 0.37228, 0.37228), (-0.00388, 0.37228, -0.00388), (-0.00388, 0.37228, -0.00388), (-0.00388, -0.00388, -0.00388), (-0.00388, 0.37228, 0.37228), (-0.00388, 0.37228, 0.37228), (0.37228, 0.37228, -0.00388), (-0.00388, 0.37228, 0.37228), (0, 0, 0), (0, 0, 0), (0.26225, 0.26225, 0), (0, 0.26225, 0.26225), (0, 0, 0.26225), (0.26225, 0, 0), (0.26225, 0.26225, 0.26225), (0.26225, 0.26225, 0.26225)]




faces=[[0, 1, 2], [4, 5, 6], [8, 9, 10], [12, 13, 14], [16, 17, 18], [20, 21, 22], [0, 2, 3], [4, 6, 7], [8, 10, 11], [12, 14, 15], [16, 18, 19], [20, 22, 23]]


ifc_faces = []
for face in faces:
    #print (face)
    ifc_faces.append(
        file.createIfcFace(
            [
                file.createIfcFaceOuterBound(
                    file.createIfcPolyLoop(
                        [file.createIfcCartesianPoint(vertices[index]) for index in face]
                    ),
                    True,
                )
            ]
        )
    )
representation = file.createIfcProductDefinitionShape(
    None,
    None,
    [
        file.createIfcShapeRepresentation(
            context,
            "Body",
            "Brep",
            [file.createIfcFacetedBrep(file.createIfcClosedShell(ifc_faces))],
        )
    ],
)
product = file.create_entity(
    "IfcFurnishingElement",
    **{
        "GlobalId": ifcopenshell.guid.new(),
        "Name": "Wall",
        "ObjectPlacement": placement,
        "Representation": representation,
    }
)
ifcopenshell.api.run("spatial.assign_container", file, product=product, relating_structure=storey)

#file.write(path.replace(".obj", ".ifc"))
file.write("meshwalls.ifc")




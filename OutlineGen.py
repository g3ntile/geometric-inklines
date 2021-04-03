# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# Geometric Outlines Generator (W.I.P.)
# beta 0.1.0
# Pablo Gentile 04/2021
# https://github.com/g3ntile/geometric-inklines

bl_info = {
    "name": "Geometry INKlines",
    "category": "Object",
    "author": "Pablo Gentile",
    "version": (0, 1, 1),
    "blender": (2, 80, 0),
    "location": "View3D > Tool Shelf",
    "description": "Adds and administrates a combo of modifiers, vertex groups and materials to generate geometric inverted hull outlines to objects that work in realtime",
    "warning": "Still Beta",
    "wiki_url": "https://github.com/g3ntile/geometric-inklines/wiki",
    "tracker_url": "https://github.com/g3ntile/geometric-inklines" ,
}

import bpy
import mathutils
from math import radians
from bpy.app.handlers import persistent

# Handles frame by frame updating
@persistent
def my_handler(scene):
    """Handles frame by frame updating"""
    
    if scene.ink_tool.ink_constantUpdate:
        vertexGroup = scene.ink_tool.ink_vertexGroup
        print ('!update! ' + vertexGroup)
        for myobj in scene.objects:
            if vertexGroup in myobj.vertex_groups:
                updateThickness(bpy.context, myobj, vertexGroup)
                #print(myobj.name)
                print(myobj.name + ' updated at frame '+  str(scene.frame_current))
                #print(scene.frame_current)


# Converts SUN rotation into a vector
def myLampToVector(lampObj):
    """Converts the Sun rotation into a vector"""
    return( mathutils.Quaternion((
        # tries to flip the quaternion somehow to get the shadows right
        # i don't get at all what I'm doing here, this is just intuitive math 
                            -lampObj.rotation_quaternion[0], 
                            lampObj.rotation_quaternion[1], 
                            lampObj.rotation_quaternion[2],
                            lampObj.rotation_quaternion[3])) )

# Handles calculation of the thickness vertex group in relation to the light source.
def updateThickness(context, myobj, groupName):
    if myobj.type == 'MESH' or 'GPENCIL':
        # check if group exists and create it 
        if groupName in myobj.vertex_groups:
            print("yes! exists")
            myGroup = myobj.vertex_groups[groupName]
        else:
            print("nope :-( it doesn't" )
            myGroup = myobj.vertex_groups.new(name=groupName)

        # move the grpup to the top:
        if (myGroup.index) > 0:
            bpy.ops.object.vertex_group_set_active(group=myobj.vertex_groups[-1].name )
            for myiteration in range (len(myobj.vertex_groups)+1):
                bpy.ops.object.vertex_group_move(direction='UP')
    if myobj.type == 'MESH':
        ### MESH calculations
        # lights math
        # Includes light if present 9
        print ('calculating light incidence for MESH ' + myobj.name)
        myLamp = None
        
        hasLight = False
        myLightVector = mathutils.Vector((0,0,65535))

        #new method:::
        
        myLamp = context.scene.ink_tool.ink_Light
        if myLamp:
            hasLight = True
            myLightIsSun = False
            myLightVector = myLamp.location

            if myLamp.type == 'LIGHT':
                if myLamp.data.type == 'SUN':
                    myLightVector = myLamp.rotation_euler
                    myLightIsSun = True
                #else:
                    #myLightVector = myLamp.location
                    # myLightIsSun = False
        else:
            hasLight = False

        # Store the mesh
        mesh = myobj.data
        print("==== object: ", mesh.name)

        # backup rotation mode OBJECT
        rotModeBKP_ob = myobj.rotation_mode

        if hasLight:
            # backup rotation mode LIGHT
            rotModeBKP_li = myLamp.rotation_mode
        
            if not myLightIsSun:
                print(myLamp.name)
                print('\n\n\n Point!')

                #POINT lights, spot, area
                # Sets weight based on angle with light DOT version
                # take rotation into account:
                myobj.rotation_mode = 'XYZ'
                myCrossedNormals = [ myobj.rotation_euler.to_matrix() @ v.normal for v in mesh.vertices  ]

                myCrossedNormals = [ ((v.dot(myLightVector) * -1+1)/2) for v in myCrossedNormals ]
                myWeights = [ ((v)) for v in myCrossedNormals]
            else: 
                print('\n\n\n Sun!')
                # FOR SUN LIGHTS
                # ROTATE OBJ OPPOSITE TO LIGHT
                            #rotModeBKP_ob = bpy.context.active_object.rotation_mode
                            #rotModeBKP_li = myLamp.rotation_mode

                # change mode to quaternion to avoid glitches and locks and simplify math
                myLamp.rotation_mode = 'QUATERNION'
                myobj.rotation_mode = 'QUATERNION'
                rotationBackup = ((
                                    myobj.rotation_quaternion[0] , 
                                    myobj.rotation_quaternion[1] , 
                                    myobj.rotation_quaternion[2] ,
                                    myobj.rotation_quaternion[3]))

                
                # multiply the quaternion of the obj with some sort of flipped quaternion of the lamp
                # WIP
                myobj.rotation_quaternion =   myLampToVector(myLamp) @ myobj.rotation_quaternion #myLamp.rotation_quaternion #


                ########. vertex normals according to world::
                #Actually it is, when the scaling factors are not the same (as @mifth pointed out) :
                # for v in bpy.context.active_object.data.vertices:
                #     myCrossedNormals[v] = v.normal.to_4d()
                #     myCrossedNormals[v].w = 0
                #     myCrossedNormals[v] = (bpy.context.active_object.matrix_world @ myCrossedNormals).to_3d()

                # If you know they are all the same, you can use :
                myobj.rotation_mode = 'XYZ'
                myCrossedNormals = [ myobj.rotation_euler.to_matrix() @ v.normal for v in mesh.vertices  ]
                
                #print( "\n\nto matrix: " , myCrossedNormals)
                myWeights = [ ((-v[2]+1)/2 ) for v in myCrossedNormals]


                # Restore rotation 
                myobj.rotation_mode = 'QUATERNION'
                myobj.rotation_quaternion = rotationBackup
                myobj.rotation_mode = rotModeBKP_ob
                

                
            #restore rotation mode LIGHT
            myLamp.rotation_mode = rotModeBKP_li
        else: 
            
            print('\n\n\n No light!')
            
            # take rotation into account:
            myobj.rotation_mode = 'XYZ'
            myCrossedNormals = [ myobj.rotation_euler.to_matrix() @ v.normal for v in mesh.vertices  ]
            
            # Sets weight based on vertex z normal
            myWeights = [ ((-v[2]+1)/2) for v in myCrossedNormals]
            #myWeights = [ ((-v.normal[2]+1)/2) for v in mesh.vertices] 
        
        # restore rotations
        myobj.rotation_mode = rotModeBKP_ob
        ### myLamp.rotation_mode = rotModeBKP_li 
        
        # Get the index of the required group
        index = myobj.vertex_groups[groupName].index

        # Exit Edit mode or fails
        ###### bpy.ops.object.mode_set(mode='OBJECT')

        # Sets the calculated weights to each vertex in the mesh
        for v in mesh.vertices:
            #print ("i = ", i)
            # print ("v = ", v)
            # print ("w = ", myWeights[v.index]) 
            #obj.vertex_groups[index].add([v], myWeights[v], 'REPLACE')
            myGroup.add([v.index], myWeights[v.index], 'REPLACE')

        # Assign the map to the Outline if it exists
        try:
            myobj.modifiers["Outline"].vertex_group = groupName
        except:
            pass
        myobj.data.update() 

    elif myobj.type == 'GPENCIL':
        print ('GPENCIL, no calculation needed')
    # Update to show results  
    
    print(myobj.name + ' updated at frame '+  str(context.scene.frame_current))


# Objeto que guarda las variables del panel
class Ink_settings(bpy.types.PropertyGroup):
    # bl_idname = "scene.Ink_settings"
    # bl_label = "ink settings"
    inkFloat: bpy.props.FloatProperty(
        name='inkFloat',
        default=0.0
    )

    ink_constantUpdate: bpy.props.BoolProperty(
        name='update each frame',
        description="All thickness maps are updated every frame. Slower.", 
        default=False
    )
    ink_Light: bpy.props.PointerProperty(
        name='source' ,
        description="Object used as light source for the thickness calculation. Sun lamps affect width by its angle of incidence. All other sources affect by position in relation to the object. \nAny object may be light source.",
        type=bpy.types.Object
    )
    ink_vertexGroup: bpy.props.StringProperty(
        name='ink vertex group',
        description='The vertex group used to store the thickness values',
        default='__thickness__'
    )



# =================================== OPERATORS =======================
# ÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷
# ÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷ ADD OUTLINE OPERATOR 

class genOutline(bpy.types.Operator):
    """Adds a Solidify modifier for making inverted hull outlines"""
    bl_idname = "object.geoink_outline"
    bl_label = "add Outline"

    C = bpy.context
    #obj = bpy.context.active_object
    #ob = obj

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        C = context
        C.space_data.shading.show_backface_culling = True
        vertexGroup = C.scene.ink_tool.ink_vertexGroup


        #iterate the active object in selected
        for obj in C.selected_objects:
            C.view_layer.objects.active = obj

            bpy.ops.object.modifier_add(type='SOLIDIFY')
            obj.modifiers[len(C.object.modifiers)-1].name = "Outline"
            obj.modifiers["Outline"].material_offset = 16384
            obj.modifiers["Outline"].use_flip_normals = 1
            obj.modifiers["Outline"].thickness = .01
            obj.modifiers["Outline"].offset = 1
            obj.modifiers["Outline"].show_expanded = False
            obj.modifiers["Outline"].thickness_vertex_group = 0.5
            obj.modifiers["Outline"].vertex_group = vertexGroup
            obj.modifiers["Outline"].offset = 1
        
        return {'FINISHED'}
    
# ÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷  Remove Outline Operator
class genNoOutline(bpy.types.Operator):
    """Removes the inverted hull Outlines"""
    bl_idname = "object.geoink_no_outline"
    bl_label = "remove Outline"

    C = bpy.context
    #obj = bpy.context.active_object
    #ob = obj

    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None
    
    def execute(self, context):
        C = bpy.context
        for obj in C.selected_objects:

            obj.modifiers.remove(obj.modifiers.get("Outline"))
        
        return {'FINISHED'}
    
    
# ÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷ ADD INLINE OPERATOR 

class genInnerline(bpy.types.Operator):
    """Adds a Bevel modifier for making geometric inner lines"""
    bl_idname = "object.geoink_innerline"
    bl_label = "add inner lines"

    C = bpy.context
    #obj = bpy.context.active_object
    #ob = obj

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):

        C = bpy.context
        #iterate the active object in selected
        for obj in C.selected_objects:
            C.view_layer.objects.active = obj
            bpy.ops.object.modifier_add(type='BEVEL')
            obj.modifiers[len(C.object.modifiers)-1].name = "InnerLine"
            obj.modifiers["InnerLine"].material = 1
            obj.modifiers["InnerLine"].offset_type = 'PERCENT'
            obj.modifiers["InnerLine"].width = 1
            obj.modifiers["InnerLine"].limit_method = 'ANGLE'
            obj.modifiers["InnerLine"].show_expanded = False
        return {'FINISHED'}
    
# ÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷ Remove Inner line Operator
class genNoInnerline(bpy.types.Operator):
    """Removes the beveled innerlines"""
    bl_idname = "object.geoink_no_innerline"
    bl_label = "remove innerline"

    C = bpy.context
    #obj = bpy.context.active_object
    #ob = obj

    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None
    
    def execute(self, context):
        C = bpy.context
        for obj in C.selected_objects:
            obj.modifiers.remove(obj.modifiers.get("InnerLine"))
        
        return {'FINISHED'}
    
# ÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷ set up thickness maps 
class genNormals2Thickness(bpy.types.Operator):
    """Generates a normals based thickness map to control the stroke thickness variation of the outlines. Select only objects to generate vertical thickness maps, or include ONE light in the selection to make it relative to the light position."""
    bl_idname = "object.geoink_normals2thick"
    bl_label = "generate thickness map"

    C = bpy.context
    #obj = bpy.context.active_object
    #ob = obj

    
    @classmethod
    def poll(cls, context):
        return context is not None
    
    def execute(self, context):
        vertexGroup = context.scene.ink_tool.ink_vertexGroup

        # itera todos los objetos seleccionados
        for myobj in context.selected_objects:
            updateThickness(context, myobj, vertexGroup)

            

        return {'FINISHED'}

############################################################################################################
# Materials creator
class genAddOutlineMaterial(bpy.types.Operator):
    """Adds a Material to make outlines"""
    bl_idname = "object.geoink_addoutlinemat"
    bl_label = "add outlines materials"

    C = bpy.context
    #obj = bpy.context.active_object
    #ob = obj
    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None
    
    def execute(self, context):
        C = context
        print('Creating materials')
        # scenesetup(context)

        ## ob = bpy.context.active_object

        # Get material. 
        # if it doesn't exist create it
        outMat = bpy.data.materials.get("outline")
        if outMat is None:
            # create  outline material
            outMat = bpy.data.materials.new(name="outline")
            outMat.use_nodes = True
            # enable transparency
            outMat.blend_method = 'BLEND'
            # no shadows
            outMat.shadow_method = 'NONE'
            # set vewport color
            outMat.diffuse_color = (0,0,0,1)

            # get the nodes
            nodes = outMat.node_tree.nodes
            print("\n\n === " , nodes)

            #start clean
            for node in nodes:
                nodes.remove(node)

            # create output node
            node_output = nodes.new(type='ShaderNodeOutputMaterial')   
            node_output.location = 400,0

            # create Mix node 1
            node_mix_1 = nodes.new(type='ShaderNodeMixShader')   
            node_mix_1.location = 0,0

            # create Mix node 2
            node_mix_2 = nodes.new(type='ShaderNodeMixShader')   
            node_mix_2.location = -200,50

            # create emission node
            node_emission = nodes.new(type='ShaderNodeEmission')
            node_emission.inputs[0].default_value = (0,0,0,1)  # black RGBA
            node_emission.inputs[1].default_value = 0 # strength
            node_emission.location = -400,220

            # create Geometry node
            node_geometry = nodes.new(type='ShaderNodeNewGeometry')   
            node_geometry.location = -400,110

            # create Transparent node
            node_transparent = nodes.new(type='ShaderNodeBsdfTransparent')   
            node_transparent.location = -400,-420

            # create LightPath node
            node_lightpath = nodes.new(type='ShaderNodeLightPath')   
            node_lightpath.location = -400,-110




            # link nodes
            links = outMat.node_tree.links
            # MIX 1 -> OUTPUT
            link = links.new(node_mix_1.outputs[0], node_output.inputs[0])
            # MIX 2 -> MIX 1
            link = links.new(node_mix_2.outputs[0], node_mix_1.inputs[1])
            # EMISSION -> MIX 2
            link = links.new(node_emission.outputs[0], node_mix_2.inputs[1])
            # GEOMETRY -> MIX 2
            link = links.new(node_geometry.outputs[6], node_mix_2.inputs[0])
            # TRANSPARENT -> MIX 2
            link = links.new(node_transparent.outputs[0], node_mix_2.inputs[2])
            # TRANSPARENT -> MIX 1
            link = links.new(node_transparent.outputs[0], node_mix_1.inputs[1])
            # LIGHT PATH -> MIX 1
            link = links.new(node_lightpath.outputs[0], node_mix_1.inputs[0])
            # MIX 1 -> MIX 2
            link = links.new(node_mix_2.outputs[0], node_mix_1.inputs[2])


        #iterate the active object in selected
        for ob in context.selected_objects:
            
            # Assign material to object
            if ob.data.materials:
                # assign to 1st material slot
                ob.data.materials.append(outMat)
            else:
                # no slots
                # dummy main material:
                dummyMat = bpy.data.materials.new(name="Material")
                ob.data.materials.append(dummyMat)
                dummyMat.use_nodes = True
                ob.data.materials.append(outMat)

            #

        # SETS BACKFACE CULLING
        # bpy.data.screens["Layout"].shading.show_backface_culling = True

        return {'FINISHED'}


# GP version
# class genGPOutlines(bpy.types.Operator):

#     bpy.ops.object.gpencil_add(align='WORLD', location=(0, 0, 0), scale=(1, 1, 1), type='LRT_SCENE')



    ######################################
    ################# PANEL
    
class genOutlinesPanel(bpy.types.Panel):
    """Creates a Panel in the N Panel"""
    bl_label = "Geometry INKlines 0.1.1"
    bl_idname = "OBJECT_PT_GEOINKlines"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = "objectmode"
    bl_category = "GEO Inklines"
    #bl_options = {'DEFAULT_CLOSED'} 

    C = bpy.context

    def draw(self, context):
        layout = self.layout


        obj = bpy.context.object
        C = bpy.context
        scene = context.scene

        # my custom properties
        ink_tool = context.scene.ink_tool

        row = layout.row()

        col = layout.column()
        
        col.prop(ink_tool, "ink_Light")
        col.prop(ink_tool, "ink_vertexGroup")
       
        # outline material generator
        row = layout.row() 
        row.operator("object.geoink_addoutlinemat")

        
        # thickness map generator
        row = layout.row() 
        row.operator("object.geoink_normals2thick" , text="generate thickness map")
       
        # add Buttons
        row = layout.row()
        
        # check if theres already an Outline
        myOperator = "object.geoink_outline"
        myLabel = "add Outline"
        hasOutline = False
        for modifier in C.object.modifiers:
            if modifier.name == "Outline":
                myOperator = "object.geoink_no_outline"
                myLabel = "remove Outline"
                hasOutline = True
                
        row.operator(myOperator, text = myLabel)
            
            
        # check if theres already an innerLine
        myOperator = "object.geoink_innerline"
        myLabel = "add Inner Line"
        hasInline = False
        for modifier in C.object.modifiers:
            if modifier.name == "InnerLine":
                hasInline = True
                myOperator = "object.geoink_no_innerline"
                myLabel = "remove Inner Line"
        
        row.operator(myOperator, text = myLabel)
        
        # edit buttons
        # --- thickness
        row = layout.row()
        if hasOutline:
            row.prop(C.object.modifiers['Outline'], "thickness", text="Outer thickness")
        if hasInline:
            row.prop(C.object.modifiers['InnerLine'], "width", text="Inner thickness")
        
        # --- contrast
        row = layout.row()
        try:
            row.prop(C.object.modifiers['Outline'], "thickness_vertex_group", text="Outline flatness")
        except Exception: 
            pass
        row = layout.row()
        try:
            row.prop(C.object.modifiers['InnerLine'], "angle_limit", text="inner lines angle")
        except Exception: 
            pass
        # --- offset
        row = layout.row()
        try:
            row.prop(C.object.modifiers['Outline'], "offset", text="Outline offset")
        except Exception: 
            pass

        row = layout.row()
        try:
            row.prop(C.object.modifiers['Outline'], "material_offset", text="Outline material offset")
        except Exception: 
            pass
        try:
            row.prop(C.object.modifiers['InnerLine'], "material", text="Inner line material offset")
        except Exception: 
            pass

        col = layout.column()
        col.prop(ink_tool, "ink_constantUpdate")



# ################################################################

#                         R E G I S T E R 

# ################################################################


classes = (
    Ink_settings,
    genOutline,
    genInnerline,
    genNoOutline,
    genNoInnerline,
    genNormals2Thickness,
    genAddOutlineMaterial,
    genOutlinesPanel
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.ink_tool = bpy.props.PointerProperty(type=Ink_settings)
    bpy.app.handlers.frame_change_pre.append(my_handler)
    print ('Geo INKLines registered!')

def unregister():
    bpy.app.handlers.frame_change_pre.append(my_handler)
    del bpy.types.Scene.ink_tool
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    print ('Geo INKLines unregistered!')


if __name__ == "__main__":
    # scenesetup(context)
    register()


bl_info = {
    "name": "Lazy Motion Edit",
    "author": "Hirotaka Imagawa",
    "version": (1, 0, 0),
    "blender": (2, 75, 0),
    "location": "Properties > Object Buttons",
    "description": "Edit motion by G, R, S",
    "category": "Animation",
}

import bpy
import mathutils
import math
import time
from bpy.types import (
    Operator,
    Panel,
    UIList,
)

from bpy.props import (
    StringProperty,
    FloatProperty,
    BoolProperty,
    EnumProperty,
)

class LazyMotionEditModePanel(bpy.types.Panel):
    bl_label = "Lazy Motion Edit"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        wm = context.window_manager
        layout = self.layout

        if not hasattr(wm, "lazy_motionedit_type"):
            layout.label("Scene does not have a property 'lazy_motionedit_type'")
 
        elif wm.lazy_motionedit_type != 'None':
            layout.label("motion-edit : " + wm.lazy_motionedit_type, icon="COLOR_GREEN")
 
        else:
            layout.label(wm.lazy_motionedit_type)

        layout = self.layout
        row = layout.row()
        row.prop(wm, "lazy_motionedit_type", expand=True)


def motionedit_update(self, context):
    wm = context.window_manager
    print("motionedit_update() invoked : " + str(wm.lazy_motionedit_type))
    if wm.lazy_motionedit_type == 'Smooth' or wm.lazy_motionedit_type == 'Increase' or wm.lazy_motionedit_type == 'Decrease':
        print("creating fcurve for motion-edit Smooth")
        for obj in bpy.context.selected_objects:
            anim = obj.animation_data
            if anim is None or anim.action is None:
                print("%s has no actions"%(obj.name))
                #print("motion-edit mode cancelled. has no fcurves to edit")
                #wm.lazy_motionedit_type = 'None'
            else:
                print("%s has some actions"%(obj.name))
                dpath = "motionedit_curve"
                fc_mec = anim.action.fcurves.find(dpath, index=0)
                if fc_mec is None:
                    print("%s : path : %s not found\n" % (obj.name, dpath))
                    if wm.lazy_motionedit_type == 'Smooth':
                        obj.motionedit_curve = 0.0
                        obj.keyframe_insert(data_path="motionedit_curve", frame=0)
                        obj.motionedit_curve = 1.0
                        obj.keyframe_insert(data_path="motionedit_curve", frame=15)
                        obj.motionedit_curve = 0.0
                        obj.keyframe_insert(data_path="motionedit_curve", frame=30)
                    elif wm.lazy_motionedit_type == 'Increase':
                        obj.motionedit_curve = 0.0
                        obj.keyframe_insert(data_path="motionedit_curve", frame=0)
                        obj.motionedit_curve = 0.5
                        obj.keyframe_insert(data_path="motionedit_curve", frame=15)
                        obj.motionedit_curve = 1.0
                        obj.keyframe_insert(data_path="motionedit_curve", frame=30)
                    elif wm.lazy_motionedit_type == 'Decrease':
                        obj.motionedit_curve = 1.0
                        obj.keyframe_insert(data_path="motionedit_curve", frame=0)
                        obj.motionedit_curve = 0.5
                        obj.keyframe_insert(data_path="motionedit_curve", frame=15)
                        obj.motionedit_curve = 0.0
                        obj.keyframe_insert(data_path="motionedit_curve", frame=30)
                else:
                    if len(fc_mec.keyframe_points) < 3:
                        continue
                    if wm.lazy_motionedit_type == 'Smooth':
                        fc_mec.keyframe_points[0].co[1] = 0.0
                        fc_mec.keyframe_points[1].co[1] = 1.0
                        fc_mec.keyframe_points[2].co[1] = 0.0
                    if wm.lazy_motionedit_type == 'Increase':
                        fc_mec.keyframe_points[0].co[1] = 0.0
                        fc_mec.keyframe_points[1].co[1] = 0.5
                        fc_mec.keyframe_points[2].co[1] = 1.0
                    if wm.lazy_motionedit_type == 'Decrease':
                        fc_mec.keyframe_points[0].co[1] = 1.0
                        fc_mec.keyframe_points[1].co[1] = 0.5
                        fc_mec.keyframe_points[2].co[1] = 0.0

                    fc_mec.keyframe_points[0].handle_left_type = 'AUTO_CLAMPED'
                    fc_mec.keyframe_points[1].handle_left_type = 'AUTO_CLAMPED'
                    fc_mec.keyframe_points[2].handle_left_type = 'AUTO_CLAMPED'
                    fc_mec.keyframe_points[0].handle_right_type = 'AUTO_CLAMPED'
                    fc_mec.keyframe_points[1].handle_right_type = 'AUTO_CLAMPED'
                    fc_mec.keyframe_points[2].handle_right_type = 'AUTO_CLAMPED'
                    fc_mec.update()
        

class LazyMotionEditProperties(Panel):
    bl_label = "Lazy Motion Edit Prop"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(context.object, "motionedit_curve")


class LazyMotionEditSlerpPose(object):

    def __init__(self):
        self.poses_pre = {}
        self.poses_post = {}
        self.poses_quat_diff = {}
        self.poses_pos_diff = {}
        self.operator = None
        self.obj = None

    def set_poses_pre(self):
        if self.is_in_motionedit() == False:
            return
        self.poses_pre = {}
        self.set_poses(self.poses_pre)

    def set_poses_post(self):
        if self.is_in_motionedit() == False:
            return
        self.poses_post = {}
        self.set_poses(self.poses_post)

    def set_poses(self, poses):
        for key in self.operator.me_ids.keys():
            if self.obj.type == 'ARMATURE':
                if key in self.obj.pose.bones:
                    pbone = self.obj.pose.bones[key]
                    pos = pbone.location.copy()
                    quat = pbone.rotation_quaternion.copy()
                    poses[pbone.name] = (pos, quat)
            else:
                self.obj = bpy.context.scene.objects[key]
                pos = self.obj.location.copy()
                quat = self.obj.rotation_quaternion.copy()
                poses[self.obj.name] = (pos, quat)

        '''
        for key, (pos, quat) in poses.items():
            print("name : " + str(key))
            print("location : " + str(pos))
            print("rotation_quaternion : " + str(quat))
        '''

    def slerp_pose(self):
        if self.is_in_motionedit() == False:
            return

        self.set_poses_post()
        self.set_poses_diff()

    def set_poses_diff(self):
        if self.is_in_motionedit() == False:
            return
        scene = bpy.context.scene

        # store the differences for pos and quat
        self.poses_quat_diff = {}
        self.poses_pos_diff = {}
        for key, (pos0, quat0) in self.poses_pre.items():
            (pos1, quat1) = self.poses_post[key]
            pos_diff = pos1 - pos0
            quat_diff = quat1 - quat0

            self.poses_quat_diff[key] = quat_diff
            self.poses_pos_diff[key] = pos_diff

        # apply difference to rotation_quaternion
        for key, quat_diff in self.poses_quat_diff.items():
            if quat_diff.w == 0 and quat_diff.x == 0 and quat_diff.y == 0 and quat_diff.z == 0:
                continue
            if self.obj.type == 'ARMATURE':
                e = self.obj.pose.bones[key]
                data_path = 'pose.bones["%s"].rotation_quaternion' % e.name
                anim = self.obj.animation_data
            else:
                e = bpy.context.scene.objects[key]
                data_path = 'rotation_quaternion'
                anim = e.animation_data

            if anim is None or anim.action is None:
                self.operator.report({'WARNING'}, "%s has no actions"%(self.obj.name))
                continue

            fc_w = anim.action.fcurves.find(data_path, index=0)
            if fc_w is None:
                self.operator.report({'WARNING'}, "%s : path : %s not found\n" % (e.name, data_path))
                continue

            fc_x = anim.action.fcurves.find(data_path, index=1)
            fc_y = anim.action.fcurves.find(data_path, index=2)
            fc_z = anim.action.fcurves.find(data_path, index=3)
            for (key_w, key_x, key_y, key_z) in zip(fc_w.keyframe_points, fc_x.keyframe_points, fc_y.keyframe_points, fc_z.keyframe_points):
                t, w = key_w.co
                if t < scene.frame_preview_start or scene.frame_preview_end < t:
                    continue
                t, x = key_x.co
                t, y = key_y.co
                t, z = key_z.co
                q_curr = mathutils.Quaternion((w, x, y, z))
                q_curr = self.apply_diff(anim, q_curr, quat_diff, t)
                key_w.co[1] = q_curr.w
                key_x.co[1] = q_curr.x
                key_y.co[1] = q_curr.y
                key_z.co[1] = q_curr.z
                key_w.handle_left_type = 'AUTO_CLAMPED'
                key_x.handle_left_type = 'AUTO_CLAMPED'
                key_y.handle_left_type = 'AUTO_CLAMPED'
                key_z.handle_left_type = 'AUTO_CLAMPED'
                key_w.handle_right_type = 'AUTO_CLAMPED'
                key_x.handle_right_type = 'AUTO_CLAMPED'
                key_y.handle_right_type = 'AUTO_CLAMPED'
                key_z.handle_right_type = 'AUTO_CLAMPED'
                fc_w.update()
                fc_x.update()
                fc_y.update()
                fc_z.update()

        # apply difference to location
        for key, pos_diff in self.poses_pos_diff.items():
            if pos_diff.x == 0 and pos_diff.y == 0 and pos_diff.z == 0:
                continue

            if self.obj.type == 'ARMATURE':
                e = self.obj.pose.bones[key]
                data_path = 'pose.bones["%s"].location' % e.name
                anim = self.obj.animation_data
            else:
                e = bpy.context.scene.objects[key]
                data_path = 'location'
                anim = e.animation_data

            if anim is None or anim.action is None:
                self.operator.report({'WARNING'}, "%s has no actions"%(self.obj.name))
                continue

            fc_x = anim.action.fcurves.find(data_path, index=0)
            fc_y = anim.action.fcurves.find(data_path, index=1)
            fc_z = anim.action.fcurves.find(data_path, index=2)
            if not (fc_x and fc_y and fc_z):
                self.operator.report({'WARNING'}, "%s : path : %s not found\n" % (e.name, data_path))
                continue

            for (key_x, key_y, key_z) in zip(fc_x.keyframe_points, fc_y.keyframe_points, fc_z.keyframe_points):
                t, x = key_x.co
                if t < scene.frame_preview_start or scene.frame_preview_end < t:
                    continue
                
                t, y = key_y.co
                t, z = key_z.co
                p_curr = mathutils.Vector((x, y, z))
                p_curr = self.apply_diff(anim, p_curr, pos_diff, t)
                key_x.co[1] = p_curr.x
                key_y.co[1] = p_curr.y
                key_z.co[1] = p_curr.z
                key_x.handle_left_type = 'AUTO_CLAMPED'
                key_y.handle_left_type = 'AUTO_CLAMPED'
                key_z.handle_left_type = 'AUTO_CLAMPED'
                key_x.handle_right_type = 'AUTO_CLAMPED'
                key_y.handle_right_type = 'AUTO_CLAMPED'
                key_z.handle_right_type = 'AUTO_CLAMPED'
                fc_x.update()
                fc_y.update()
                fc_z.update()


    def apply_diff(self, anim, v0, v_diff, frame):
        if self.lazy_motionedit_type() == 'Constant':
            return v0 + v_diff
        else:
            fc_mec = anim.action.fcurves.find("motionedit_curve", index=0)
            if fc_mec is None:
                self.operator.report({'WARNING'}, "motionedit_curve not found. done nothing")
                return v0
            weight = fc_mec.evaluate(frame)
            return v0 + weight * v_diff

    def lazy_motionedit_type(self):
        wm = bpy.context.window_manager
        if not hasattr(wm, "lazy_motionedit_type"):
            self.operator.report({'WARNING'}, "Scene does not have a property 'lazy_motionedit_type'")
            return 'None'
        return wm.lazy_motionedit_type

    def is_in_motionedit(self):
        wm = bpy.context.window_manager
        if not hasattr(wm, "lazy_motionedit_type"):
            self.operator.report({'WARNING'}, "Scene does not have a property 'lazy_motionedit_type'")
            return False
        elif wm.lazy_motionedit_type == 'None':
            self.operator.report({'WARNING'}, "motion edit : None. Done nothing")
            return False
        else:
            self.operator.report({'WARNING'}, "motion edit : %s"%(wm.lazy_motionedit_type))
            return True


class LazyMotionEditHandleTransformOperator(bpy.types.Operator):
    bl_idname = "motionedit.handle_transform_operator"
    bl_label = "Lazy Motion Edit Handle Transform Operator"
    
    operatorName = bpy.props.StringProperty("")
    slerpPose = LazyMotionEditSlerpPose()
    obj = None
    count = 0

    def set_ids(self):
        self.me_ids = {}

        if self.obj.type == 'ARMATURE':
            id = 0
            for bone in self.obj.pose.bones:
                self.me_ids[bone.name] = id
                id = id + 1
        else:
            id = 0
            for selObj in bpy.context.selected_objects:
                self.me_ids[selObj.name] = id
                id = id + 1

    def modal(self, context, event):
        # DRAG START
        self.count += 1
        if self.count == 1: # once in the loop
            self.slerpPose.set_poses_pre()
            actObj = bpy.context.active_object
            if self.operatorName == "Translate_POS":
                self.report({'INFO'}, "%s(LazyMotionEdit)" % ("Translate_POS"))
                bpy.ops.transform.translate('INVOKE_DEFAULT')
            if self.operatorName == "Rotate":                
                self.report({'INFO'}, "%s(LazyMotionEdit)" % ("Rotate"))
                bpy.ops.transform.rotate('INVOKE_DEFAULT')
            if self.operatorName == "Scale":                
                self.report({'INFO'}, "%s(LazyMotionEdit)" % ("Scale"))
                bpy.ops.transform.resize('INVOKE_DEFAULT')

        # DRAG FINISHED
        if event.type == 'LEFTMOUSE':
            actObj = bpy.context.active_object
            # APPLY in current MOTION MODE
            self.slerpPose.slerp_pose()
            self.report({'INFO'}, "Lazy Motion Edit Transform Operator FINISHED")
            return {'FINISHED'}

        # DRAG CANCELLED
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            actObj = bpy.context.active_object
            self.report({'INFO'}, "Lazy Motion Edit Transform Operator CANCELLED")
            return {'CANCELLED'}
        
        return {'RUNNING_MODAL'}
        
    def invoke(self, context, event):
        if context.object is None:
            self.report({'WARNING'}, "No active object. cancelled.")
            return {'CANCELLED'}

        self.slerpPose.obj = self.obj = bpy.context.active_object
        self.slerpPose.operator = self

        if self.slerpPose.is_in_motionedit() == True:
            self.set_ids()
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            if self.operatorName == "Translate_POS":
                self.report({'INFO'}, "%s(Native)" % ("Translate"))
                bpy.ops.transform.translate('INVOKE_DEFAULT')
            if self.operatorName == "Rotate":                
                self.report({'INFO'}, "%s(Native)" % ("Rotate"))
                bpy.ops.transform.rotate('INVOKE_DEFAULT')
            if self.operatorName == "Scale":                
                self.report({'INFO'}, "%s(Native)" % ("Scale"))
                bpy.ops.transform.resize('INVOKE_DEFAULT')
            return {'FINISHED'}


# properties used by the script
def init_properties():
    wm = bpy.types.WindowManager
    itemlist = [
    #order: (identifier, name, description, icon, unique number)
    ('None', '', 'None', 'RADIOBUT_OFF', 0),
    ('Constant', '', 'Constant', 'NOCURVE', 1),
    ('Smooth', '', 'Smooth', 'SMOOTHCURVE', 2),
    ('Increase', '', 'Increase', 'ZOOMIN', 3),
    ('Decrease', '', 'Decrease', 'ZOOMOUT', 4)
    ]
    wm.lazy_motionedit_type = bpy.props.EnumProperty(name="lazy_motionedit_type", description="motion-edit type", default="None", items=itemlist, update=motionedit_update)


# removal of properties when script is disabled
def clear_properties():
    props = (
        "lazy_motionedit_type",
    )
    wm = bpy.context.window_manager
    for p in props:
        if p in wm:
            del wm[p]


addon_keymaps = []

classes = (
    LazyMotionEditModePanel,
    LazyMotionEditProperties,
    LazyMotionEditHandleTransformOperator,
)

def register():
    init_properties()
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Object.motionedit_curve = FloatProperty(name="motionedit_curve", default=1.0, min=0.0, max=1)

    wm = bpy.context.window_manager

    # create km
    km = wm.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D') # scary ... 

    # override Translate, Rotate
    kmi = km.keymap_items.new(LazyMotionEditHandleTransformOperator.bl_idname, 'G', 'PRESS')
    kmi.properties.operatorName = "Translate_POS"
    addon_keymaps.append((km, kmi))

    kmi = km.keymap_items.new(LazyMotionEditHandleTransformOperator.bl_idname, 'R', 'PRESS')
    kmi.properties.operatorName = "Rotate"
    addon_keymaps.append((km, kmi))
    

def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    for cls in classes:
        bpy.utils.unregister_class(cls)

    clear_properties()

if __name__ == "__main__":
    register()

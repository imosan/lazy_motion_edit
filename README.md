# lazy_motion_edit

blender addon

This addon overrirdes blender native short-cuts 'G', 'R'.
These behave same as native behaviour in "None" mode. It will just translation or rotation.
You can change whole keys between start(preview) and end(preview) by trarnslate or rotate in "Constant" or "Smooth" mode.

When you translate or rotate an object in 3DView, this addon script adds the dragged value into all the associated fcurves. This means that this addon changes default translation and rotation to a tool as a 'lazy motion editor'.

This may be usefull when you want to translate or rotate an object already has fcuves.

You can also apply the translation or rotation to the object with "motionedit_curve". This curve will be created automatically when the mode is changed to "Smooth". The curve will be used as a weight. 

![alt tag](https://github.com/imosan/motion_edit/blob/master/lazy_motion_edit_1.jpg)

"Increase" and "Decrease" changes the first three keys in "motionedit_curve".
This addon also works on pose bones in Armature object.

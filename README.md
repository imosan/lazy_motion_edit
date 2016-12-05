# motion_edit

blender addon

This addon overrirdes blender native short-cuts 'G', 'R'.
Their behaviours are the completely same as native's in "None" mode.
You can change whole keys between start(preview) and end(preview) by trarnslate or rotate in "Constant" or "Smooth" mode.

When you translate or rotate an object in 3DView, this addon script adds the dragged value into all the associated fcurves as a 'lazy motion editing' tool.

You can also apply the translation or rotation to the object with "motionedit_curve". This curve will be created automatically when the mode is changed to "Smooth". The curve will be used as a weight. 

![alt tag](https://github.com/imosan/motion_edit/blob/master/motion_edit_1.jpg)

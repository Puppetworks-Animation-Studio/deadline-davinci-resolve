# DaVinci Resolve Deadline
DaVinci Resolve plugin for Thinkbox Deadline.

## Features
Open a DaVinci Resolve project on Deadline, and render to a specific location.

## Requirements
* Studio version of DaVinci Resolve. **It won't work with the free version**. Tested with 16.1.
* Tested with Thinkbox Deadline 8, but it should work with 9/10 too.

## Installation
Copy the `DaVinciResolve` folder to the `custom/plugins` folder of your Deadline installation.

If you installed DaVinci in a custom location, set the `Resolve` and `fuscript` executables through `Tools/Configure Plugins/DaVinciResolve` 

## Limitations
* Since there is no API in DaVinci to manage the project database, the plugin can only work on the last opened one. 
Make sure to have only one centralized project database opened on your slaves.
* DaVinci uses custom Qt dialogs, that Deadline cannot catch with `AddPopupHandler`, so make sure when opening a DaVinci project
it does not pop up an error dialog like the no permission for cache/gallery/capture paths.
You can avoid it by setting these paths to a shared drive. You probably also have to set as the first path the Media Storage in preferences ([more info](https://forum.blackmagicdesign.com/viewtopic.php?f=21&t=58481)). 

## Usage
Submit a job with `DaVinciResolve` plugin type and the following plugin parameters:
* `ProjectName`: The name of the DaVinci project to load. 
* `Folders` (optional): Folders to open in the current project database, where the project resides.
Can contain path separators (/ or \\), to open multiple subfolders. Example: `folder/subfolder1/subfolder2`
* `Timeline` (optional): Name of the timeline to set as current.
* `OutputPath`: File path to render to. This path is put through a `datetime.now().strftime()` so it can contain any [formatting tag](https://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior).
Example: `c:/temp/output_%Y%m%d-%H%M.mov` results in `c:/temp/output_20200103-1539.mov`
* `RenderPreset`: (optional): Render preset to use when exporting the movie. If you are using a custom one, make sure to save it into the project file. Example: `YouTube - 1080p`
* `Format`: (optional, but Format + Codec have to be both specified to be set) Format to be used when exporting. Example: `mp4`
* `Codec`: (optional, but Format + Codec have to be both specified to be set) Codec to be used when exporting. Example: `h264` 

##### Notes
* The RenderPreset is loaded first, then the Format+Codec, so you can override these settings from the preset. 
* If any of the optional parameters are not set, the values in the project file will be used.
* If any of the parameters cannot be set, the job will fail.

### Example submission
job_info.txt file
```
Name=Test DaVinci job
Frames=1
Plugin=DaVinciResolve
```
plugin_info.txt file
```
OutputPath=c:/output/%y%m%d/auto_davinci_output_%Y%m%d-%H%M.mp4
ProjectName=masterproject
Folders=folder1
Timeline=timeline1
```
command to run: `deadlinecommand.exe job_info.txt plugin_info.txt`

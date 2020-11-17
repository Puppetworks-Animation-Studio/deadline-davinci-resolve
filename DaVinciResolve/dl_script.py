import os
import sys
import time
import argparse
from datetime import datetime

try:
    import DaVinciResolveScript as dvr_script
except ImportError:
    # sys.path.append("%PROGRAMDATA%/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/Modules")
    sys.path.append("C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/Modules")
    import DaVinciResolveScript as dvr_script


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("project_name")
    parser.add_argument("output_path")
    parser.add_argument("--folders", default="")
    parser.add_argument("--timeline", default="")
    parser.add_argument("--format", default="")
    parser.add_argument("--codec", default="")
    parser.add_argument("--render_preset", default="")
    args = parser.parse_args()

    project_name = args.project_name
    output_path = args.output_path
    folders = args.folders
    timeline_name = args.timeline
    format_ = args.format
    codec = args.codec
    render_preset = args.render_preset

    formatted_output_path = datetime.now().strftime(output_path)

    resolve = _connect_to_resolve()
    project = _load_project(resolve, project_name, folders)

    if timeline_name:
        _set_timeline(project, timeline_name)

    _setup_render_job(project, formatted_output_path, format_, codec, render_preset)
    _start_render(project)


def _connect_to_resolve():
    resolve = None
    i = 0
    while i < 5:
        resolve = dvr_script.scriptapp("Resolve")
        if resolve is not None:
            break
        print "Waiting for Resolve to start..."
        time.sleep(5)
        i += 1
    if resolve is None:
        raise RuntimeError("Could not connect to DaVinci Resolve. There may be a problem starting it, or you may be using the free version.")
    print "wait a bit more for resolve to become responsible"
    time.sleep(5)
    return resolve


def _load_project(resolve, project_name, folders):
    project_manager = resolve.GetProjectManager()
    if folders:
        folders = folders.replace("\\", "/")
        for folder in folders.split("/"):
            print "Opening folder:", folder
            assert project_manager.OpenFolder(folder), "Cannot open folder."
    print "Loading project:", project_name
    assert project_manager.LoadProject(project_name), "Cannot load project."
    project = project_manager.GetCurrentProject()
    print project
    return project


def _set_timeline(project, timeline_name):
    for i in xrange(int(project.GetTimelineCount())):  # GetTimelineCount returns float...
        timeline = project.GetTimelineByIndex(i + 1)  # index starts from 1
        # print timeline.GetName()
        if timeline.GetName() == timeline_name:
            print "Setting current timeline to", timeline.GetName()
            assert project.SetCurrentTimeline(timeline), "Cannot set timeline."


def _setup_render_job(project, formatted_output_path, format_="", codec="", render_preset=""):
    assert project.DeleteAllRenderJobs(), "Cannot delete render jobs..."

    print "Loading render preset [{}]".format(render_preset)
    assert project.LoadRenderPreset(render_preset), "Cannot set render_preset [{}]".format(render_preset)

    render_settings = {
        # "SelectAllFrames": ?,
        # "MarkIn": ?,
        # "MarkOut": ?,
        "TargetDir": os.path.dirname(formatted_output_path),
        "CustomName": os.path.basename(formatted_output_path)
    }
    assert project.SetRenderSettings(render_settings), "Cannot set render settings..."

    if format_ and codec:
        assert project.SetCurrentRenderFormatAndCodec(format_, codec), "Cannot set render format/codec."

    assert project.AddRenderJob(), "Cannot add render job..."


def _start_render(project):
    assert project.StartRendering(1)
    while project.IsRenderingInProgress():
        print project.GetRenderJobStatus(1)
        # sys.stdout.flush()
        time.sleep(1)
    print project.GetRenderJobStatus(1)


if __name__ == '__main__':
    main()

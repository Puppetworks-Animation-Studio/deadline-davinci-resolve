import time
from FranticX.Processes import *
from Deadline.Plugins import *
from Deadline.Scripting import *
from System.IO import *

RESOLVE_PROCESS_NAME = "DaVinci Resolve Process"
FUSCRIPT_PROCESS_NAME = "FuScript Process"

__version__ = "0.1.0"


def GetDeadlinePlugin():
    return DaVinciResolvePlugin()


def CleanupDeadlinePlugin(deadlinePlugin):
    deadlinePlugin.Cleanup()


class DaVinciResolvePlugin(DeadlinePlugin):
    def __init__(self):
        self.InitializeProcessCallback += self.InitializeProcess
        self.StartJobCallback += self.StartJob
        self.RenderTasksCallback += self.RenderTasks
        self.EndJobCallback += self.EndJob

    def Cleanup(self):
        del self.InitializeProcessCallback
        del self.StartJobCallback
        del self.RenderTasksCallback
        del self.EndJobCallback

    # noinspection PyAttributeOutsideInit
    def InitializeProcess(self):
        self.SingleFramesOnly = True
        self.PluginType = PluginType.Advanced

    def StartJob(self):
        process = ResolveProcess(self)
        self.StartMonitoredManagedProcess(RESOLVE_PROCESS_NAME, process)
        self.SetStatusMessage("Waiting to start")

    def RenderTasks(self):
        fuscript_process = FuScriptProcess(self)
        self.StartMonitoredManagedProcess(FUSCRIPT_PROCESS_NAME, fuscript_process)
        self.SetMonitoredManagedProcessExitCheckingFlag(FUSCRIPT_PROCESS_NAME, True)
        self.FlushMonitoredManagedProcessStdout(RESOLVE_PROCESS_NAME)

        while not self.WaitForMonitoredManagedProcessToExit(FUSCRIPT_PROCESS_NAME, 1000):
            self.FlushMonitoredManagedProcessStdout(FUSCRIPT_PROCESS_NAME)
            self.FlushMonitoredManagedProcessStdout(RESOLVE_PROCESS_NAME)

            # blockingDialogMessage = self.CheckForMonitoredManagedProcessPopups(RESOLVE_PROCESS_NAME)
            # if (blockingDialogMessage != ""):
            #     self.FailRender(blockingDialogMessage)

            # self.FlushFusionOutput(False)

            # blockingDialogMessage = self.CheckForMonitoredManagedProcessPopups(RESOLVE_PROCESS_NAME)
            # if (blockingDialogMessage != ""):
            #     self.FailRender(blockingDialogMessage)

            # self.VerifyMonitoredManagedProcess(RESOLVE_PROCESS_NAME)

            if self.IsCanceled():
                self.FailRender("Received cancel task command")

        self.FlushMonitoredManagedProcessStdout(FUSCRIPT_PROCESS_NAME)
        self.FlushMonitoredManagedProcessStdout(RESOLVE_PROCESS_NAME)

        fuscript_exit_code = self.GetMonitoredManagedProcessExitCode(FUSCRIPT_PROCESS_NAME)
        self.LogInfo("Fuscript returned exit code " + str(fuscript_exit_code))
        if fuscript_exit_code != 0:
            self.FailRender("Fuscript exited before finishing, it may have been terminated externally")

    def EndJob(self):
        self.ShutdownMonitoredManagedProcess(RESOLVE_PROCESS_NAME)


class ResolveProcess(ManagedProcess):
    def __init__(self, deadline_plugin):
        self.deadline_plugin = deadline_plugin
        self.RenderExecutableCallback += self.RenderExecutable
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderArgumentCallback += self.RenderArgument

        self.PopupHandling = True
        self.HandleQtPopups = True
        self.PopupMaxChildWindows = 50
        # self.HandleWindows10Popups = True

        self.SetEnvironmentVariable("QT_USE_NATIVE_WINDOWS", "1")
        self.PopupButtonClasses = ("Qt5QWindowIcon",)
        self.AddPopupHandler(".*", "QPushButtonClassWindow")
        # self.AddPopupIgnorer(".*")

    def Cleanup(self):
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback

    def InitializeProcess(self):
        pass

    def RenderExecutable(self):
        return self.deadline_plugin.GetConfigEntry("ResolveExecutable")

    def RenderArgument(self):
        return "-nogui"


class FuScriptProcess(ManagedProcess):
    def __init__(self, deadline_plugin):
        self.deadline_plugin = deadline_plugin
        self.RenderExecutableCallback += self.RenderExecutable
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderArgumentCallback += self.RenderArgument

        self.SetEnvironmentVariable("PYTHONUNBUFFERED", "1")

        self.StdoutHandling = True
        self.AddStdoutHandlerCallback(".*'CompletionPercentage': (\d*)\..*'JobStatus': 'Rendering'").HandleCallback += self.HandleProgress
        self.AddStdoutHandlerCallback(".*'JobStatus': 'Failed', 'Error': '(.+)'").HandleCallback += self.HandleJobError
        self.AddStdoutHandlerCallback("Traceback").HandleCallback += self.HandleTraceback

    def Cleanup(self):
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback

    def InitializeProcess(self):
        pass

    def RenderExecutable(self):
        # return "python.exe"
        return self.deadline_plugin.GetConfigEntry("FuScriptExecutable")

    def RenderArgument(self):
        project_name = self.deadline_plugin.GetPluginInfoEntry("ProjectName")
        output_path = self.deadline_plugin.GetPluginInfoEntry("OutputPath")
        folders = self.deadline_plugin.GetPluginInfoEntryWithDefault("Folders", "")
        timeline = self.deadline_plugin.GetPluginInfoEntryWithDefault("Timeline", "")
        format_ = self.deadline_plugin.GetPluginInfoEntryWithDefault("Format", "")
        codec = self.deadline_plugin.GetPluginInfoEntryWithDefault("Codec", "")
        render_preset = self.deadline_plugin.GetPluginInfoEntryWithDefault("RenderPreset", "")

        dl_script = Path.Combine(self.deadline_plugin.GetPluginDirectory(), "dl_script.py")

        args = ['"{}" "{}" "{}"'.format(dl_script, project_name, output_path)]

        if folders:
            args.append('--folders "{}"'.format(folders))

        if timeline:
            args.append('--timeline "{}"'.format(timeline))

        if format_:
            args.append('--format "{}"'.format(format_))

        if codec:
            args.append('--codec "{}"'.format(codec))

        if render_preset:
            args.append('--render_preset "{}"'.format(render_preset))

        return " ".join(args)

    def HandleProgress(self):
        progress = int(self.GetRegexMatch(1))
        self.deadline_plugin.SetProgress(progress)
        self.deadline_plugin.SetStatusMessage("Rendering")

    def HandleJobError(self):
        message = self.GetRegexMatch(1)
        self.deadline_plugin.AbortRender(message)

    def HandleTraceback(self):
        self.deadline_plugin.FlushMonitoredManagedProcessStdout(FUSCRIPT_PROCESS_NAME)
        self.deadline_plugin.AbortRender("The execution of the script failed. Check the log for the error.")

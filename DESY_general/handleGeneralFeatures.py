#!/usr/bin/env python
"""
the general hooks/conditions/on_stop macro interface:
the feature is used in gscan.py, scan.py and macro.py

14.6.2018: this file is OK for the old and new Sardana version
"""
from sardana.macroserver.macro import Macro, Type
import HasyUtils

__all__ = ["gf_status",
           # "gf_list", "gf_head",
           "gf_enable",
           "gh_enable", "gh_disable", "gh_isEnabled",
           "gc_enable", "gc_enable", "gc_isEnabled"]

#
# status for all features
#
class gf_status(Macro):
    """display the status of the general features:
          hooks, conditions, on_stop """

    def run(self):
        self.output("Status general features:")
        self.output("")
        #
        # hooks
        #
        if HasyUtils.versionSardanaNewMg():
            self.execMacro("lsgh")
        else:
            self.execMacro("gh_isEnabled")

        self.output("")

        #
        # condition
        #
        self.execMacro("gc_isEnabled")

        self.output("")
        #
        # on-stop
        #
        self.execMacro("gs_isEnabled")


#
# general feature
#
class gf_enable(Macro):
    """enable all general features: hooks, conditions, on_stop """

    def run(self):
        self.execMacro("gh_enable")
        self.execMacro("gc_enable")
        self.execMacro("gs_enable")


class gf_disable(Macro):
    """disable all general features: hooks, conditions, on_stop """

    def run(self):
        self.execMacro("gc_disable")
        self.execMacro("gh_disable")
        self.execMacro("gs_disable")

        self.info("All general features disabled")


#
# general hooks feature
#
class gh_enable(Macro):
    """
    enable general hooks

      spock> gh_enable
        enables all hooks

      spock> gh_enable someMacro pre-scan
        someMacro will be executed during pre-scan

    hook positions: defaultMacroNames:
        pre-scan: gh_pre_scan, pre-move: gh_pre_move, post-move: gh_post_move,
        pre-acq: gh_pre_acq, post-acq: gh_post_acq,
        post-step: gh_post_step, post-scan: gh_post_scan
    """

    param_def = [
        ['macro_name', Type.String, "default",
         'Macro name executed at hook_pos, e.g. gh_pre_scan'],
        ['hook_pos', Type.String, "default",
         'Position where the macro_name is executed, e.g. pre-scan'],
    ]

    def gh_enableD9(self, macro_name, hook_pos):
        '''
        for the new sardana version, uses _GeneralHooks, defgh, udefgh, lsgh
        '''
        hookDct = {"pre-scan": "gh_pre_scan",
                   "pre-move": "gh_pre_move",
                   "post-move": "gh_post_move",
                   "pre-acq": "gh_pre_acq",
                   "post-acq": "gh_post_acq",
                   "post-step": "gh_post_step",
                   "post-scan": "gh_post_scan"}

        #
        # 'gh_enable' without args: reset everything
        #
        if hook_pos == 'default':
            macros_list = []
            for hook in hookDct.keys():
                hook_tuple = (hookDct[hook], [hook])
                macros_list.append(hook_tuple)
            #
            # [('gh_pre_scan', ['pre-scan']),
            #      ('gh_post_scan', ['post-scan']), ...)]
            #
            self.debug("gh_enable: %s" % repr(macros_list))
            self.setEnv("_GeneralHooks", macros_list)
            return

        #
        # hook_pos can be e.g. pre-scan
        #
        if hook_pos not in hookDct.keys():
            self.error("gh_enable(D9): hook %s not in dictionary" % hook_pos)
            return
        #
        # check, if macro_name exists on the MacroServer
        #
        if macro_name not in self.getMacroNames():
            self.error("gh_enable(D9): macro %s does not exist" % macro_name)
            return

        self.execMacro('defgh', macro_name, [hook_pos])
        return

    def gh_enableD8(self, macro_name, hook_pos):
        '''
        the old sardana version, uses GeneralHooks
        GeneralHooks:
          {'post-scan': ['gh_post_scan'],
           'post-step': ['gh_post_step'],
           'post-acq': ['gh_post_acq'],
           'post-move': ['gh_post_move'],
           'pre-scan': ['gh_pre_scan'],
           'pre-acq': ['gh_pre_acq'],
           'pre-move': ['gh_pre_move']}
        '''
        default_dict = {'pre-scan': ['gh_pre_scan'],
                        'pre-move': ['gh_pre_move'],
                        'pre-acq': ['gh_pre_acq'],
                        'post-acq': ['gh_post_acq'],
                        'post-move': ['gh_post_move'],
                        'post-step': ['gh_post_step'],
                        'post-scan': ['gh_post_scan']}

        #
        # default hooks
        #
        if hook_pos == "default":
            if macro_name != 'default':
                self.error(
                    "gh_enableD8: a macro name (%s) must not be "
                    "specified without a hook name" % macro_name)
                return

            self.info("Enabling all general hooks with default macro names")
            self.debug("gh_enableD8: %s" % repr(default_dict))
            self.setEnv("GeneralHooks", default_dict)
            return

        #
        # valid hook name?
        #
        if hook_pos not in default_dict.keys():
            self.error("gh_enableD8: wrong hook name, possible values:")
            self.error(str(default_dict.keys()))
            return
        #
        # check, if macro_name exists on the MacroServer
        #
        if macro_name not in self.getMacroNames():
            self.error("gh_enable(D9): macro %s does not exist" % macro_name)
            return

        try:
            gh_macros_dict = self.getEnv("GeneralHooks")
        except Exception:
            gh_macros_dict = {}

        macro_name_split = macro_name.split(",")
        gh_macros_dict[hook_pos] = []
        for name in macro_name_split:
            gh_macros_dict[hook_pos].append(name)
        self.debug("gh_enableD8: %s" % repr(gh_macros_dict))
        self.setEnv("GeneralHooks", gh_macros_dict)
        return

    #
    #
    #
    def run(self, macro_name, hook_pos):

        if HasyUtils.versionSardanaNewMg():
            self.gh_enableD9(macro_name, hook_pos)
            return
        else:
            self.gh_enableD8(macro_name, hook_pos)
            return


class gh_disable(Macro):
    """disable general hooks """

    param_def = [
        ['hook_pos', Type.String, "all",
         'Position of the general hook to be disabled'],
    ]

    def gh_disableD9(self, hook_pos):

        hookDct = {"pre-scan": "gh_pre_scan",
                   "pre-move": "gh_pre_move",
                   "post-move": "gh_post_move",
                   "pre-acq": "gh_pre_acq",
                   "post-acq": "gh_post_acq",
                   "post-step": "gh_post_step",
                   "post-scan": "gh_post_scan"}

        try:
            gh_macros_list = self.getEnv("_GeneralHooks")
        except Exception:
            return

        if hook_pos == 'all':
            self.unsetEnv("_GeneralHooks")
            self.info("Undefine all general hooks")
            return

        if hook_pos not in hookDct.keys():
            self.error(
                "gh_disable (D9): hook_pos %s not in dictionary" % hook_pos)
            return

        #
        # [('gh_pre_scan', ['pre-scan']),
        #        ('gh_post_scan', ['post-scan']), ...)]
        #
        macros_list = []
        for elm in gh_macros_list:
            #
            # ('gh_pre_scan', ['pre-scan'])
            #
            if hook_pos not in elm[1]:
                macros_list.append(elm)

        self.debug("gh_disable: %s" % repr(macros_list))
        self.setEnv("_GeneralHooks", macros_list)

    def gh_disableD8(self, hook_pos):

        try:
            gh_macros_dict = self.getEnv("GeneralHooks")
        except Exception:
            return

        if hook_pos == "all":
            self.unsetEnv("GeneralHooks")
            self.info("All hooks disabled")
        else:
            if hook_pos not in gh_macros_dict.keys():
                self.info(
                    "gh_disableD8: %s not an allowed hook name" % hook_pos)
                return

            try:
                del gh_macros_dict[hook_pos]
                self.info("Hook %s disabled" % hook_pos)
            except Exception:
                self.info("gh_disableD8: failed to delete %s" % hook_pos)
                return

            self.setEnv("GeneralHooks", gh_macros_dict)

    def run(self, hook_pos):

        if HasyUtils.versionSardanaNewMg():
            self.gh_disableD9(hook_pos)
        else:
            self.gh_disableD8(hook_pos)

        return


class gh_isEnabled(Macro):
    """
    return True, if hook_pos enabled
    return True, if no hook_pos is specified and at least one hook is enabled
    """

    param_def = [
        ['hook_pos', Type.String, "any",
         'Hook to be checked, e.g. pre-scan, default: any'],
    ]

    result_def = [["result", Type.Boolean, None,
                   "True, if the general hooks feature is enabled"]]

    def gh_isEnabledD9(self, hook_pos):

        try:
            gh_macros_list = self.getEnv("_GeneralHooks")
        except Exception:
            return False
        #
        # _GeneralHooks exists. If hook_poos == 'any':
        #        If there is some contents, return True
        #
        if hook_pos == 'any':
            if len(gh_macros_list) == 0:
                return False

            self.execMacro("lsgh")
            return True
        #
        # [('gh_pre_scan', ['pre-scan']),
        #           ('gh_post_scan', ['post-scan']), ...)]
        #

        # macros_list = []
        for elm in gh_macros_list:
            #
            # ('gh_pre_scan', ['pre-scan'])
            #
            if hook_pos in elm[1]:
                return True

        return False

    def gh_isEnabledD8(self, hook_pos):

        try:
            general_hooks = self.getEnv("GeneralHooks")
        except Exception:
            self.output("No general hooks")
            return False

        #
        # GeneralHooks exists.
        # If hook_poos == 'any' and there is some contents, return True
        #
        if hook_pos == 'any':
            if len(general_hooks) == 0:
                return False

            for k in general_hooks.keys():
                self.output(k)
                self.output(str(general_hooks[k]))
            return True
        #
        # GeneralHooks:
        #  {'post-scan': ['gh_post_scan'], 'post-step': ['gh_post_step'], ...}
        #
        if hook_pos in general_hooks.keys():
            return True
        else:
            return False

    def run(self, hook_pos):
        result = False

        if HasyUtils.versionSardanaNewMg():
            result = self.gh_isEnabledD9(hook_pos)
        else:
            result = self.gh_isEnabledD8(hook_pos)

        return result


#
# general condition feature
#
class gc_enable(Macro):
    """enable general conditions """

    param_def = [
        ['macro_name', Type.String, "default", 'Macro name with parameters']]

    def run(self, macro_name):
        if macro_name == "default":
            self.setEnv("GeneralCondition", "gc_macro")
        else:
            self.setEnv("GeneralCondition", macro_name)


class gc_disable(Macro):
    """disable general conditions """

    def run(self):
        try:
            self.unsetEnv("GeneralCondition")
        except Exception:
            pass


class gc_isEnabled(Macro):
    """return True, if the general conditions feature is enabled """

    result_def = [["result", Type.Boolean, None,
                   "True, if the general condition feature is enabled"]]

    def run(self):
        result = False

        try:
            general_condition = self.getEnv("GeneralCondition")
            self.output("Selected general condition:")
            self.output(general_condition)
            return True
        except Exception:
            self.output("No general condition")

        return result


#
# on_stop feature
#
class gs_enable(Macro):
    """enable on_stop feature """

    param_def = [
        ['function_name', Type.String, "default",
         'Function name with module and parameters']]

    def run(self, function_name):
        if function_name == "default":
            self.setEnv("GeneralOnStopFunction",
                        "general_functions.general_on_stop")
        else:
            self.setEnv("GeneralOnStopFunction", function_name)


class gs_disable(Macro):
    """disable on_stop feature """

    def run(self):
        try:
            self.unsetEnv("GeneralOnStopFunction")
        except Exception:
            pass


class gs_isEnabled(Macro):
    """return True, if the general on_stop feature is enabled """

    result_def = [["result", Type.Boolean, None,
                   "True, if the general on_stop feature is enabled"]]

    def run(self):
        result = False

        try:
            general_on_stop = self.getEnv("GeneralOnStopFunction")
            self.output("Selected general on_stop:")
            self.output(general_on_stop)
            return True
        except Exception:
            self.output("No general on_stop")

        return result

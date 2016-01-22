# -*- coding: iso-8859-1 -*-
"""
(c) 2012-2015 Martin Wendt; see https://github.com/mar10/pyftpsync
Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
"""

from __future__ import print_function

import fnmatch
import sys
import time
from datetime import datetime

from ftpsync.targets import IS_REDIRECTED, DRY_RUN_PREFIX, DirMetadata,\
    ansi_code, console_input
from ftpsync.resources import FileEntry, DirectoryEntry

def _ts(timestamp):
    return "{0} ({1})".format(datetime.fromtimestamp(timestamp), timestamp)

DEFAULT_OMIT = [".DS_Store",
                ".git",
                ".hg",
                ".svn",
                DirMetadata.META_FILE_NAME,
                DirMetadata.LOCK_FILE_NAME,
                ]


#===============================================================================
# BaseSynchronizer
#===============================================================================
class BaseSynchronizer(object):
    """Synchronizes two target instances in dry_run mode (also base class for other synchronizers)."""

    _resolve_shortcuts = {"l": "local", "r": "remote", "s": "skip"}

    def __init__(self, local, remote, options):
        self.local = local
        self.remote = remote
        #TODO: check for self-including paths
        self.options = options or {}
        self.verbose = self.options.get("verbose", 3)
        self.dry_run = self.options.get("dry_run", True)

        self.include_files = self.options.get("include_files")
        if self.include_files:
            self.include_files = [ pat.strip() for pat in self.include_files.split(",") ]

        self.omit = self.options.get("omit")
        if self.omit:
            self.omit = [ pat.strip() for pat in self.omit.split(",") ]

        self.local.synchronizer = self
        self.local.peer = remote
        self.remote.synchronizer = self
        self.remote.peer = local
        if self.dry_run:
            self.local.readonly = True
            self.local.dry_run = True
            self.remote.readonly = True
            self.remote.dry_run = True
        if not local.connected:
            local.open()
        if not remote.connected:
            remote.open()

        self.resolve_all = None

        self._stats = {"bytes_written": 0,
                       "conflict_files": 0,
                       "dirs_created": 0,
                       "dirs_deleted": 0,
                       "download_bytes_written": 0,
                       "download_files_written": 0,
                       "elap_secs": None,
                       "elap_str": None,
                       "entries_seen": 0,
                       "entries_touched": 0,
                       "files_created": 0,
                       "files_deleted": 0,
                       "files_written": 0,
                       "local_dirs": 0,
                       "local_files": 0,
                       "meta_bytes_read": 0,
                       "meta_bytes_written": 0,
                       "remote_dirs": 0,
                       "remote_files": 0,
                       "upload_bytes_written": 0,
                       "upload_files_written": 0,
                       }

    def get_stats(self):
        return self._stats

    def _inc_stat(self, name, ofs=1):
        self._stats[name] = self._stats.get(name, 0) + ofs

    def _match(self, entry):
        name = entry.name
        if name == DirMetadata.META_FILE_NAME:
            return False
#        if name in self.DEFAULT_OMIT:
#            return False
        ok = True
        if entry.is_file() and self.include_files:
            ok = False
            for pat in self.include_files:
                if fnmatch.fnmatch(name, pat):
                    ok = True
                    break
        if ok and self.omit:
            for pat in self.omit:
                if fnmatch.fnmatch(name, pat):
                    ok = False
                    break
        return ok

    def run(self):
        start = time.time()

        info_strings = self.get_info_strings()
        print("{0} {1}\n{2:>20} {3}".format(info_strings[0].capitalize(),
                                            self.local.get_base_name(),
                                            info_strings[1],
                                            self.remote.get_base_name()))

        res = self._sync_dir()

        stats = self._stats
        stats["elap_secs"] = time.time() - start
        stats["elap_str"] = "%0.2f sec" % stats["elap_secs"]

        def _add(rate, size, time):
            if stats.get(time) and stats.get(size):
                stats[rate] = "%0.2f kb/sec" % (.001 * stats[size] / stats[time])
        _add("upload_rate_str", "upload_bytes_written", "upload_write_time")
        _add("download_rate_str", "download_bytes_written", "download_write_time")
        return res

    def _copy_file(self, src, dest, file_entry):
        # TODO: save replace:
        # 1. remove temp file
        # 2. copy to target.temp
        # 3. use loggingFile for feedback
        # 4. rename target.temp
#        print("_copy_file(%s, %s --> %s)" % (file_entry, src, dest))
        assert isinstance(file_entry, FileEntry)
        self._inc_stat("files_written")
        self._inc_stat("entries_touched")
        is_upload = (dest is self.remote)
        if is_upload:
            self._inc_stat("upload_files_written")
        else:
            self._inc_stat("download_files_written")
        self._tick()
        if self.dry_run:
            return self._dry_run_action("copy file (%s, %s --> %s)" % (file_entry, src, dest))
        elif dest.readonly:
            raise RuntimeError("target is read-only: %s" % dest)

        start = time.time()
        def __block_written(data):
#            print(">(%s), " % len(data))
            self._inc_stat("bytes_written", len(data))
            if is_upload:
                self._inc_stat("upload_bytes_written", len(data))
            else:
                self._inc_stat("download_bytes_written", len(data))

        with src.open_readable(file_entry.name) as fp_src:
            dest.write_file(file_entry.name, fp_src, callback=__block_written)

#         dest.set_mtime(file_entry.name, file_entry.get_adjusted_mtime(), file_entry.size)
#         dest.set_sync_info(file_entry.name, file_entry.get_adjusted_mtime(), file_entry.size)
        dest.set_mtime(file_entry.name, file_entry.mtime, file_entry.size)
        dest.set_sync_info(file_entry.name, file_entry.mtime, file_entry.size)

        elap = time.time() - start
        self._inc_stat("write_time", elap)
        if is_upload:
            self._inc_stat("upload_write_time", elap)
        else:
            self._inc_stat("download_write_time", elap)
        return

    def _copy_recursive(self, src, dest, dir_entry):
#        print("_copy_recursive(%s, %s --> %s)" % (dir_entry, src, dest))
        assert isinstance(dir_entry, DirectoryEntry)
        self._inc_stat("entries_touched")
        self._inc_stat("dirs_created")
        self._tick()
        if self.dry_run:
            return self._dry_run_action("copy directory (%s, %s --> %s)" % (dir_entry, src, dest))
        elif dest.readonly:
            raise RuntimeError("target is read-only: %s" % dest)

        dest.set_sync_info(dir_entry.name, None, None)

        src.push_meta()
        dest.push_meta()

        src.cwd(dir_entry.name)
        dest.mkdir(dir_entry.name)
        dest.cwd(dir_entry.name)
        dest.cur_dir_meta = DirMetadata(dest)
        for entry in src.get_dir():
            # the outer call was already accompanied by an increment, but not recursions
            self._inc_stat("entries_seen")
            if entry.is_dir():
                self._copy_recursive(src, dest, entry)
            else:
                self._copy_file(src, dest, entry)

        src.flush_meta()
        dest.flush_meta()

        src.cwd("..")
        dest.cwd("..")

        src.pop_meta()
        dest.pop_meta()
        return

    def _remove_file(self, file_entry):
        # TODO: honor backup
#        print("_remove_file(%s)" % (file_entry, ))
        assert isinstance(file_entry, FileEntry)
        self._inc_stat("entries_touched")
        self._inc_stat("files_deleted")
        if self.dry_run:
            return self._dry_run_action("delete file (%s)" % (file_entry,))
        elif file_entry.target.readonly:
            raise RuntimeError("target is read-only: %s" % file_entry.target)
        file_entry.target.remove_file(file_entry.name)
        file_entry.target.remove_sync_info(file_entry.name)

    def _remove_dir(self, dir_entry):
        # TODO: honor backup
        assert isinstance(dir_entry, DirectoryEntry)
        self._inc_stat("entries_touched")
        self._inc_stat("dirs_deleted")
        if self.dry_run:
            return self._dry_run_action("delete directory (%s)" % (dir_entry,))
        elif dir_entry.target.readonly:
            raise RuntimeError("target is read-only: %s" % dir_entry.target)
        dir_entry.target.rmdir(dir_entry.name)
        dir_entry.target.remove_sync_info(dir_entry.name)

    def _log_call(self, msg, min_level=5):
        if self.verbose >= min_level:
            print(msg)

    # https://github.com/tartley/colorama/blob/master/colorama/ansi.py
#     COLOR_MAP = {("skip", "*"): ansi_code("Fore.LIGHTBLACK_EX"),
#                  ("*", "equal"): ansi_code("Fore.LIGHTBLACK_EX"),#colorama.Fore.WHITE + colorama.Style.DIM,
#                  ("skip", "conflict"): ansi_code("Fore.LIGHTRED_EX"),  # + ansi_code("Style.BRIGHT"),
#                  ("delete", "*"): ansi_code("Fore.RED"),
#                  ("*", "modified"): ansi_code("Fore.BLUE"),
#                  ("restore", "*"): ansi_code("Fore.BLUE"),
#                  ("copy", "new"): ansi_code("Fore.GREEN"),
#                  }

    def _log_action(self, action, status, symbol, entry, min_level=3):
        if self.verbose < min_level:
            return

        if len(symbol) > 1 and symbol[0] in (">", "<"):
            symbol = " " + symbol # make sure direction characters are aligned at 2nd column
        if self.options.get("no_color"):
            color = ""
            final = ""
        else:
#             CM = self.COLOR_MAP
#             color = CM.get((action, status),
#                            CM.get(("*", status),
#                                   CM.get((action, "*"),
#                                          "")))
            if action in ("copy", "restore"):
                if "<" in symbol:
                    color = ansi_code("Fore.GREEN") + ansi_code("Style.BRIGHT") if status == "new" else ansi_code("Fore.GREEN")
                else:
                    color = ansi_code("Fore.CYAN") + ansi_code("Style.BRIGHT") if status == "new" else ansi_code("Fore.CYAN")
            elif action == "delete":
                color = ansi_code("Fore.RED")
            elif status == "conflict":
                color = ansi_code("Fore.LIGHTRED_EX")
            elif action == "skip" or status == "equal":
                color = ansi_code("Fore.LIGHTBLACK_EX")

            final = ansi_code("Style.RESET_ALL")

        final += " " * 10
        prefix = ""
        if self.dry_run:
            prefix = DRY_RUN_PREFIX
        if action and status:
            tag = ("%s %s" % (action, status)).upper()
        else:
            tag = ("%s%s" % (action, status)).upper()
        name = entry.get_rel_path()
        if entry.is_dir():
            name = "[%s]" % name

#         print("{0}{1:<16} {2:^3} {3}".format(prefix, tag, symbol, name))
        print("{0}{1}{2:<16} {3:^3} {4}{5}".format(prefix, color, tag, symbol, name, final))

    def _tick(self):
        """Write progress info and move cursor to beginning of line."""
        if (self.verbose >= 3 and not IS_REDIRECTED) or self.options.get("progress"):
            stats = self.get_stats()
            prefix = DRY_RUN_PREFIX if self.dry_run else ""
            sys.stdout.write("%sTouched %s/%s entries in %s dirs...\r"
                % (prefix,
                   stats["entries_touched"], stats["entries_seen"],
                   stats["local_dirs"]))
        sys.stdout.flush()
        return

    def _dry_run_action(self, action):
        """"Called in dry-run mode after call to _log_action() and before exiting function."""
#        print("dry-run", action)
        return

    def _test_match_or_print(self, entry):
        """Return True if entry matches filter. Otherwise print 'skip' and return False ."""
        if not self._match(entry):
            self._log_action("skip", "unmatched", "-", entry, min_level=4)
            return False
        return True

    def _before_sync(self, entry):
        """Called by the synchronizer for each entry.
        Return False to prevent the synchronizer's default action.
        """
        self._inc_stat("entries_seen")
        self._tick()
        return True

    def _is_conflict(self, local, remote):
        """Return True if this is a conflict, i.e. both targets are modified."""
        any_entry = local or remote
        if any_entry.is_dir():
            # Currently we cnnot detect directory conflicts
            return False
        if local and remote:
            is_conflict = local.was_modified_since_last_sync() and remote.was_modified_since_last_sync()
        elif local:
            # remote was deleted, but local was modified
            existed = local.get_sync_info()
            is_conflict = existed and local.was_modified_since_last_sync()
        else:
            assert remote
            # local was deleted, but remote was modified
            existed = remote.get_sync_info()
            is_conflict = existed and remote.was_modified_since_last_sync()

        if is_conflict:
            self._inc_stat("conflict_files")

        return is_conflict

    def _sync_dir(self):
        """Traverse the local folder structure and remote peers.

        This is the core algorithm that generates calls to self.sync_XXX()
        handler methods.
        _sync_dir() is called by self.run().
        """
        local_entries = self.local.get_dir()
        local_entry_map = dict(map(lambda e: (e.name, e), local_entries))
        local_files = [e for e in local_entries if isinstance(e, FileEntry)]
        local_directories = [e for e in local_entries if isinstance(e, DirectoryEntry)]

        remote_entries = self.remote.get_dir()
        # convert into a dict {name: FileEntry, ...}
        remote_entry_map = dict(map(lambda e: (e.name, e), remote_entries))

        conflict_list = []

        # 1. Loop over all local files and classify the relationship to the
        #    peer entries.
        for local_file in local_files:
            self._inc_stat("local_files")
            if not self._before_sync(local_file):
                # TODO: currently, if a file is skipped, it will not be
                # considered for deletion on the peer target
                continue
            # TODO: case insensitive?
            # We should use os.path.normcase() to convert to lowercase on windows
            # (i.e. if the FTP server is based on Windows)
            remote_file = remote_entry_map.get(local_file.name)

            if self._is_conflict(local_file, remote_file):
                conflict_list.append( (local_file, remote_file) )
            elif remote_file is None:
                self._log_call("sync_missing_remote_file(%s)" % local_file)
                self.sync_missing_remote_file(local_file)
            elif local_file == remote_file:
                self._log_call("sync_equal_file(%s, %s)" % (local_file, remote_file))
                self.sync_equal_file(local_file, remote_file)
            # TODO: renaming could be triggered, if we find an existing
            # entry.unique with a different entry.name
#            elif local_file.key in remote_keys:
#                self._rename_file(local_file, remote_file)
            elif local_file > remote_file:
                self._log_call("sync_newer_local_file(%s, %s)" % (local_file, remote_file))
                self.sync_newer_local_file(local_file, remote_file)
            elif local_file < remote_file:
                self._log_call("sync_older_local_file(%s, %s)" % (local_file, remote_file))
#                 print (local_file < remote_file)
                self.sync_older_local_file(local_file, remote_file)
            else:
                self._log_call("_sync_error(%s, %s)" % (local_file, remote_file))
                self._sync_error("file with identical date but different otherwise",
                                 local_file, remote_file)

        # 2. Handle all local directories that do NOT exist on remote target.
        for local_dir in local_directories:
            self._inc_stat("local_dirs")
            if not self._before_sync(local_dir):
                continue
            remote_dir = remote_entry_map.get(local_dir.name)
            if not remote_dir:
                self._log_call("sync_missing_remote_dir(%s)" % local_dir)
                self.sync_missing_remote_dir(local_dir)

        # 3. Handle all remote entries that do NOT exist on the local target.
        for remote_entry in remote_entries:
            if isinstance(remote_entry, DirectoryEntry):
                self._inc_stat("remote_dirs")
            else:
                self._inc_stat("remote_files")

            if not self._before_sync(remote_entry):
                continue
            if not remote_entry.name in local_entry_map:
                if self._is_conflict(None, remote_entry):
                    conflict_list.append( (None, remote_entry) )
                elif isinstance(remote_entry, DirectoryEntry):
                    self._log_call("sync_missing_local_dir(%s)" % remote_entry)
                    self.sync_missing_local_dir(remote_entry)
                else:
                    self._log_call("sync_missing_local_file(%s)" % remote_entry)
                    self.sync_missing_local_file(remote_entry)

        # 4. Handle conflicts
        #    We had to postpone this, because the conflict handler may copy files
        #    in any direction, which may confuse the conflict detection above.
        for local_entry, remote_entry in conflict_list:
            self._log_call("sync_conflict(%s, %s)" % (local_entry, remote_entry))
            self.sync_conflict(local_entry, remote_entry)

        # 5. Let the target provider write its meta data for the files in the
        #    current directory.
        self.local.flush_meta()
        self.remote.flush_meta()

        # 6. Finally visit all local sub-directories recursively that also
        #    exist on the remote target.
        for local_dir in local_directories:
            if not self._before_sync(local_dir):
                continue
            remote_dir = remote_entry_map.get(local_dir.name)
            if remote_dir:
                self._log_call("sync_equal_dir(%s, %s)" % (local_dir, remote_dir))
                res = self.sync_equal_dir(local_dir, remote_dir)
                if res is not False:
                    self.local.cwd(local_dir.name)
                    self.remote.cwd(local_dir.name)
                    self._sync_dir()
                    self.local.cwd("..")
                    self.remote.cwd("..")

        return

    def _sync_error(self, msg, local_file, remote_file):
        print(msg, local_file, remote_file, file=sys.stderr)

    def sync_equal_file(self, local_file, remote_file):
        self._log_action("", "equal", "=", local_file, min_level=4)

    def sync_conflict(self, local, remote):
        self._log_action("skip", "conflict", "=", local, min_level=2)

    def sync_equal_dir(self, local_dir, remote_dir):
        """Return False to prevent visiting of children"""
        self._log_action("", "equal", "=", local_dir, min_level=4)
        return True

    def sync_newer_local_file(self, local_file, remote_file):
        self._log_action("", "modified", ">", local_file)

    def sync_older_local_file(self, local_file, remote_file):
        self._log_action("", "modified", "<", local_file)

    def sync_missing_local_file(self, remote_file):
        self._log_action("", "missing", "<", remote_file)

    def sync_missing_local_dir(self, remote_dir):
        """Return False to prevent visiting of children"""
        self._log_action("", "missing", "<", remote_dir)

    def sync_missing_remote_file(self, local_file):
        self._log_action("", "new", ">", local_file)

    def sync_missing_remote_dir(self, local_dir):
        self._log_action("", "new", ">", local_dir)


#===============================================================================
# BiDirSynchronizer
#===============================================================================
class BiDirSynchronizer(BaseSynchronizer):
    """Synchronizer that performs up- and download operations as required.

    - Newer files override unmodified older files

    - When both files are newer than last sync -> conflict!
      Conflicts may be resolved by these options::

        --resolve=old:         use the older version
        --resolve=new:         use the newer version
        --resolve=local:       use the local file
        --resolve=remote:      use the remote file
        --resolve=ask:         prompt mode

    - When a file is missing: check if it existed in the past.
      If so, delete it. Otherwise copy it.

    In order to know if a file was modified, deleted, or created since last sync,
    we store a snapshot of the directory in the local directory.
    """
    def __init__(self, local, remote, options):
        super(BiDirSynchronizer, self).__init__(local, remote, options)

    def get_info_strings(self):
        return ("synchronize", "with")

#     def _diff(self, local_file, remote_file):
#         print("    Local : %s: %s (native: %s)" % (local_file, local_file.get_adjusted_mtime(),
#             _ts(local_file.mtime)))
#         print("          : last sync %s"
#               % (local_file.get_sync_info()))
#         print("    Remote: %s: %s (native: %s)" % (remote_file, remote_file.get_adjusted_mtime(),
#             _ts(remote_file.mtime)))
#         print("          : last sync %s"
#               % (remote_file.get_sync_info()))
# #         print("    last sync: %s" % _ts(self.local.cur_dir_meta.get_last_sync()))
#         pass

    def _interactive_resolve(self, local, remote):
        """Return 'local', 'remote', or 'skip' to use local, remote resource or skip."""
        if self.resolve_all:
            return self.resolve_all
        resolve = self.options.get("resolve", "skip")
        if resolve in ("local", "remote", "skip"):
            self.resolve_all = resolve
            return resolve

        RED = ansi_code("Fore.LIGHTRED_EX")
        M = ansi_code("Style.BRIGHT") + ansi_code("Style.UNDERLINE")
        R = ansi_code("Style.RESET_ALL")

        print((RED + "CONFLICT in %s:" + R) % local.name)
        print("    local:  %s" % local.as_string())
        print("    remote: %s" % (remote.as_string() if remote else "n.a."))

        while True:
            prompt = "Use " + M + "L" + R + "ocal, use " + M + "R" + R + "emote, " + M + "S" + R + "kip, " + M + "H" + R + "elp)? "
            r = console_input(prompt).strip()
            if r in ("h", "H", "?"):
                print("The following keys are supported:")
                print("  'r': Use remote file")
                print("  'l': Use local file")
                print("  's': Skip this file (leave both versions unchanged)")
                print("Hold Shift (upper case letters) to apply choice for all remaining conflicts.")
                print("Hit Ctrl+C to abort.")
                continue
            elif r in ("L", "R", "S"):
                r = self._resolve_shortcuts[r.lower()]
                self.resolve_all = r
                break
            elif r in ("l", "r", "s"):
                r = self._resolve_shortcuts[r]
                break

        return r

    def sync_conflict(self, local_entry, remote_entry):
        if not self._test_match_or_print(local_entry or remote_entry):
            return
        resolve = self._interactive_resolve(local_entry, remote_entry)
        if resolve == "skip":
            self._log_action("skip", "conflict", "*?*", local_entry or remote_entry)
            return
        if local_entry and remote_entry:
            assert local_entry.is_file()
            is_newer = local_entry > remote_entry
            if resolve == "local" or (is_newer and resolve == "newer") or (not is_newer and resolve == "older"):
                self._log_action("copy", "conflict", "*>*", local_entry)
                self._copy_file(self.local, self.remote, local_entry)
            elif resolve == "remote" or (is_newer and resolve == "older") or (not is_newer and resolve == "newer"):
                self._log_action("copy", "conflict", "*<*", local_entry)
                self._copy_file(self.remote, self.local, remote_entry)
            else:
                raise NotImplementedError
        elif local_entry:
            assert local_entry.is_file()
            if resolve == "local":
                self._log_action("restore", "conflict", "*>x", local_entry)
                self._copy_file(self.local, self.remote, local_entry)
            elif resolve == "remote":
                self._log_action("delete", "conflict", "*<x", local_entry)
                self._remove_file(local_entry)
            else:
                raise NotImplementedError
        else:
            assert remote_entry.is_file()
            if resolve == "local":
                self._log_action("delete", "conflict", "x>*", remote_entry)
                self._remove_file(remote_entry)
            elif resolve == "remote":
                self._log_action("restore", "conflict", "x<*", remote_entry)
                self._copy_file(self.remote, self.local, remote_entry)
            else:
                raise NotImplementedError
        return

    def sync_newer_local_file(self, local_file, remote_file):
        if not self._test_match_or_print(local_file):
            return
        self._log_action("copy", "modified", "*>.", local_file)
        self._copy_file(self.local, self.remote, local_file)

    def sync_older_local_file(self, local_file, remote_file):
        if not self._test_match_or_print(local_file):
            return
        self._log_action("copy", "modified", ".<*", remote_file)
        self._copy_file(self.remote, self.local, remote_file)

    def sync_missing_local_file(self, remote_file):
        if not self._test_match_or_print(remote_file):
            return
        existed = self.local.get_sync_info(remote_file.name)
        if existed:
            self._log_action("delete", "removed", "x>.", remote_file)
            self._remove_file(remote_file)
            return
        self._log_action("copy", "new", "-<+", remote_file)
        self._copy_file(self.remote, self.local, remote_file)

    def sync_missing_local_dir(self, remote_dir):
        if not self._test_match_or_print(remote_dir):
            return
        existed = self.local.get_sync_info(remote_dir.name)
        if existed:
            self._log_action("delete", "removed", ".<x", remote_dir)
            self._remove_dir(remote_dir)
            return
        self._log_action("copy", "new", "-<+", remote_dir)
        self._copy_recursive(self.remote, self.local, remote_dir)

    def sync_missing_remote_file(self, local_file):
        if not self._test_match_or_print(local_file):
            return
        existed = local_file.get_sync_info()
        if existed:
            self._log_action("delete", "removed", ".<x", local_file)
            self._remove_file(local_file)
            return
        self._log_action("copy", "new", "+>-", local_file)
        self._copy_file(self.local, self.remote, local_file)

    def sync_missing_remote_dir(self, local_dir):
        if not self._test_match_or_print(local_dir):
            return
        existed = self.local.get_sync_info(local_dir.name)
        if existed:
            self._log_action("delete", "removed", ".<x", local_dir)
            self._remove_dir(local_dir)
            return
        self._log_action("copy", "new", "+>-", local_dir)
        self._copy_recursive(self.local, self.remote, local_dir)


#===============================================================================
# UploadSynchronizer
#===============================================================================

class UploadSynchronizer(BaseSynchronizer):

    def __init__(self, local, remote, options):
        super(UploadSynchronizer, self).__init__(local, remote, options)
        local.readonly = True

    def get_info_strings(self):
        return ("upload", "to")

    def _check_del_unmatched(self, remote_entry):
        """Return True if entry is NOT matched (i.e. excluded by filter).

        If --delete-unmatched is on, remove the remote resource.
        """
        if not self._match(remote_entry):
            if self.options.get("delete_unmatched"):
                self._log_action("delete", "unmatched", ">", remote_entry)
                if remote_entry.is_dir():
                    self._remove_dir(remote_entry)
                else:
                    self._remove_file(remote_entry)
            else:
                self._log_action("skip", "unmatched", "-", remote_entry, min_level=4)
            return True
        return False

    def _interactive_resolve(self, local, remote):
        """Return 'local', 'remote', or 'skip' to use local, remote resource or skip."""
        if self.resolve_all:
            return self.resolve_all
        resolve = self.options.get("resolve", "skip")
        assert resolve in ("local", "ask", "skip")
        if resolve in ("local", "skip"):
            self.resolve_all = resolve
            return resolve

        RED = ansi_code("Fore.LIGHTRED_EX")
        M = ansi_code("Style.BRIGHT") + ansi_code("Style.UNDERLINE")
        R = ansi_code("Style.RESET_ALL")

        print((RED + "CONFLICT in %s:" + R) % local.name)
        print("    local:  %s" % local.as_string())
        print("    remote: %s" % (remote.as_string() if remote else "n.a."))

        while True:
            prompt = "Use " + M + "L" + R + "ocal, " + M + "S" + R + "kip, " + M + "H" + R + "elp)? "
            r = console_input(prompt).strip()
            if r in ("h", "H", "?"):
                print("The following keys are supported:")
                print("  'l': Upload local file")
                print("  's': Skip this file (leave both versions unchanged)")
                print("Hold Shift (upper case letters) to apply choice for all remaining conflicts.")
                print("Hit Ctrl+C to abort.")
                continue
            elif r in ("L", "R", "S"):
                r = self._resolve_shortcuts[r.lower()]
                self.resolve_all = r
                break
            elif r in ("l", "r", "s"):
                r = self._resolve_shortcuts[r]
                break

        return r

    def sync_conflict(self, local_entry, remote_entry):
        """Both targets changed; resolve according to strategy, but never modify local."""
        if not self._test_match_or_print(local_entry or remote_entry):
            return
        resolve = self._interactive_resolve(local_entry, remote_entry)
        if resolve == "skip":
            self._log_action("skip", "conflict", "*?*", local_entry or remote_entry)
            return
        if local_entry and remote_entry:
            assert local_entry.is_file()
            is_newer = local_entry > remote_entry
            if resolve == "local" or (is_newer and resolve == "newer") or (not is_newer and resolve == "older"):
                self._log_action("copy", "conflict", "*>*", local_entry)
                self._copy_file(self.local, self.remote, local_entry)
#             elif resolve == "remote" or (is_newer and resolve == "older") or (not is_newer and resolve == "newer"):
#                 self._log_action("copy", "conflict", "*<*", local_entry)
#                 self._copy_file(self.remote, self.local, remote_entry)
            else:
                raise NotImplementedError
        elif local_entry:
            assert local_entry.is_file()
            if resolve == "local":
                self._log_action("restore", "conflict", "*>x", local_entry)
                self._copy_file(self.local, self.remote, local_entry)
#             elif resolve == "remote":
#                 self._log_action("delete", "conflict", "*<x", local_entry)
#                 self._remove_file(local_entry)
            else:
                raise NotImplementedError
        else:
            assert remote_entry.is_file()
            if resolve == "local":
                self._log_action("delete", "conflict", "x>*", remote_entry)
                self._remove_file(remote_entry)
#             elif resolve == "remote":
#                 self._log_action("restore", "conflict", "x<*", remote_entry)
#                 self._copy_file(self.remote, self.local, remote_entry)
            else:
                raise NotImplementedError
        return

    def sync_equal_file(self, local_file, remote_file):
        self._log_action("", "equal", "=", local_file, min_level=4)
        self._check_del_unmatched(remote_file)

    def sync_equal_dir(self, local_dir, remote_dir):
        """Return False to prevent visiting of children"""
        if self._check_del_unmatched(remote_dir):
            return False
        self._log_action("", "equal", "=", local_dir, min_level=4)
        return True

    def sync_newer_local_file(self, local_file, remote_file):
        if self._check_del_unmatched(remote_file):
            return False
        self._log_action("copy", "modified", ">", local_file)
        self._copy_file(self.local, self.remote, local_file)

    def sync_older_local_file(self, local_file, remote_file):
        if self._check_del_unmatched(remote_file):
            return False
        elif self.options.get("force"):
            self._log_action("restore", "older", ">", local_file)
            self._copy_file(self.local, self.remote, remote_file)
        else:
            self._log_action("skip", "older", "?", local_file, 4)

    def sync_missing_local_file(self, remote_file):
        # If a file exists locally, but does not match the filter, this will be
        # handled by sync_newer_file()/sync_older_file()
        if self._check_del_unmatched(remote_file):
            return False
        elif not self._test_match_or_print(remote_file):
            return
        elif self.options.get("delete"):
            self._log_action("delete", "missing", ">", remote_file)
            self._remove_file(remote_file)
        else:
            self._log_action("skip", "missing", "?", remote_file, 4)

    def sync_missing_local_dir(self, remote_dir):
        if self._check_del_unmatched(remote_dir):
            return False
        elif not self._test_match_or_print(remote_dir):
            return False
        elif self.options.get("delete"):
            self._log_action("delete", "missing", ">", remote_dir)
            self._remove_dir(remote_dir)
        else:
            self._log_action("skip", "missing", "?", remote_dir, 4)

    def sync_missing_remote_file(self, local_file):
        if self._test_match_or_print(local_file):
            self._log_action("copy", "new", ">", local_file)
            self._copy_file(self.local, self.remote, local_file)

    def sync_missing_remote_dir(self, local_dir):
        if self._test_match_or_print(local_dir):
            self._log_action("copy", "new", ">", local_dir)
            self._copy_recursive(self.local, self.remote, local_dir)


#===============================================================================
# DownloadSynchronizer
#===============================================================================

class DownloadSynchronizer(BaseSynchronizer):
    """
    """
    def __init__(self, local, remote, options):
        super(DownloadSynchronizer, self).__init__(local, remote, options)
        remote.readonly = True

    def get_info_strings(self):
        return ("download", "from")

    def _check_del_unmatched(self, local_entry):
        """Return True if entry is NOT matched (i.e. excluded by filter).

        If --delete-unmatched is on, remove the local resource.
        """
        if not self._match(local_entry):
            if self.options.get("delete_unmatched"):
                self._log_action("delete", "unmatched", "<", local_entry)
                if local_entry.is_dir():
                    self._remove_dir(local_entry)
                else:
                    self._remove_file(local_entry)
            else:
                self._log_action("skip", "unmatched", "-", local_entry, min_level=4)
            return True
        return False

    def _interactive_resolve(self, local, remote):
        """Return 'local', 'remote', or 'skip' to use local, remote resource or skip."""
        if self.resolve_all:
            return self.resolve_all
        resolve = self.options.get("resolve", "skip")
        assert resolve in ("remote", "ask", "skip")
        if resolve in ("remote", "skip"):
            self.resolve_all = resolve
            return resolve

        RED = ansi_code("Fore.LIGHTRED_EX")
        M = ansi_code("Style.BRIGHT") + ansi_code("Style.UNDERLINE")
        R = ansi_code("Style.RESET_ALL")

        print((RED + "CONFLICT in %s:" + R) % local.name)
        print("    local:  %s" % local.as_string())
        print("    remote: %s" % (remote.as_string() if remote else "n.a."))

        while True:
            prompt = "Use " + M + "R" + R + "emote, " + M + "S" + R + "kip, " + M + "H" + R + "elp)? "
            r = console_input(prompt).strip()
            if r in ("h", "H", "?"):
                print("The following keys are supported:")
                print("  'r': Download remote file")
                print("  's': Skip this file (leave both versions unchanged)")
                print("Hold Shift (upper case letters) to apply choice for all remaining conflicts.")
                print("Hit Ctrl+C to abort.")
                continue
            elif r in ("L", "R", "S"):
                r = self._resolve_shortcuts[r.lower()]
                self.resolve_all = r
                break
            elif r in ("l", "r", "s"):
                r = self._resolve_shortcuts[r]
                break

        return r

    def sync_conflict(self, local_entry, remote_entry):
        """Both targets changed; resolve according to strategy, but never modify remote."""
        if not self._test_match_or_print(local_entry or remote_entry):
            return
        resolve = self._interactive_resolve(local_entry, remote_entry)
        if resolve == "skip":
            self._log_action("skip", "conflict", "*?*", local_entry or remote_entry)
            return
        if local_entry and remote_entry:
            assert local_entry.is_file()
            is_newer = local_entry > remote_entry
#             if resolve == "local" or (is_newer and resolve == "newer") or (not is_newer and resolve == "older"):
#                 self._log_action("copy", "conflict", "*>*", local_entry)
#                 self._copy_file(self.local, self.remote, local_entry)
            if resolve == "remote" or (is_newer and resolve == "older") or (not is_newer and resolve == "newer"):
                self._log_action("copy", "conflict", "*<*", local_entry)
                self._copy_file(self.remote, self.local, remote_entry)
            else:
                raise NotImplementedError
        elif local_entry:
            assert local_entry.is_file()
#             if resolve == "local":
#                 self._log_action("restore", "conflict", "*>x", local_entry)
#                 self._copy_file(self.local, self.remote, local_entry)
            if resolve == "remote":
                self._log_action("delete", "conflict", "*<x", local_entry)
                self._remove_file(local_entry)
            else:
                raise NotImplementedError
        else:
            assert remote_entry.is_file()
#             if resolve == "local":
#                 self._log_action("delete", "conflict", "x>*", remote_entry)
#                 self._remove_file(remote_entry)
            if resolve == "remote":
                self._log_action("restore", "conflict", "x<*", remote_entry)
                self._copy_file(self.remote, self.local, remote_entry)
            else:
                raise NotImplementedError
        return

    def sync_equal_file(self, local_file, remote_file):
        self._log_action("", "equal", "=", local_file, min_level=4)
        self._check_del_unmatched(local_file)

    def sync_equal_dir(self, local_dir, remote_dir):
        """Return False to prevent visiting of children"""
        if self._check_del_unmatched(local_dir):
            return False
        self._log_action("", "equal", "=", local_dir, min_level=4)
        return True

    def sync_older_local_file(self, local_file, remote_file):
        if self._check_del_unmatched(local_file):
            return False
        self._log_action("copy", "modified", "<", local_file)
        self._copy_file(self.remote, self.local, remote_file)

    def sync_newer_local_file(self, local_file, remote_file):
        if self._check_del_unmatched(local_file):
            return False
        elif self.options.get("force"):
            self._log_action("restore", "older", "<", local_file)
            self._copy_file(self.remote, self.local, remote_file)
        else:
            self._log_action("skip", "older", "?", local_file, 4)

    def sync_missing_local_file(self, remote_file):
        if self._test_match_or_print(remote_file):
            self._log_action("copy", "new", "<", remote_file)
            self._copy_file(self.remote, self.local, remote_file)

    def sync_missing_local_dir(self, remote_dir):
        if self._test_match_or_print(remote_dir):
            self._log_action("copy", "new", "<", remote_dir)
            self._copy_recursive(self.remote, self.local, remote_dir)

    def sync_missing_remote_file(self, local_file):
        # If a file exists locally, but does not match the filter, this will be
        # handled by sync_newer_file()/sync_older_file()
        if self._check_del_unmatched(local_file):
            return False
        elif not self._test_match_or_print(local_file):
            return
        elif self.options.get("delete"):
            self._log_action("delete", "missing", "<", local_file)
            self._remove_file(local_file)
        else:
            self._log_action("skip", "missing", "?", local_file, 4)

    def sync_missing_remote_dir(self, local_dir):
        if self._check_del_unmatched(local_dir):
            return False
        elif not self._test_match_or_print(local_dir):
            return False
        elif self.options.get("delete"):
            self._log_action("delete", "missing", "<", local_dir)
            self._remove_dir(local_dir)
        else:
            self._log_action("skip", "missing", "?", local_dir, 4)

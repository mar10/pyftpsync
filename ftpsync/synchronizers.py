# -*- coding: utf-8 -*-
"""
(c) 2012-2020 Martin Wendt; see https://github.com/mar10/pyftpsync
Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
import fnmatch
import sys
import time

from ftpsync.ftp_target import FTPTarget
from ftpsync.metadata import DirMetadata
from ftpsync.resources import DirectoryEntry, EntryPair, FileEntry, operation_map
from ftpsync.util import (
    DRY_RUN_PREFIX,
    IS_REDIRECTED,
    VT_ERASE_LINE,
    ansi_code,
    byte_compare,
    colorama,
    eps_compare,
    pretty_stamp,
    write,
)

CONFIG_FILE_NAME = ".pyftpsync.yaml"

#: Default for --exclude CLI option
#: Note: DirMetadata.META_FILE_NAME and LOCK_FILE_NAME are always ignored
DEFAULT_OMIT = [".DS_Store", ".git", ".hg", ".svn"]
ALWAYS_OMIT = (CONFIG_FILE_NAME, DirMetadata.META_FILE_NAME, DirMetadata.LOCK_FILE_NAME)

# ===============================================================================
# Helpers
# ===============================================================================

_ts = pretty_stamp


def process_options(opts):
    """Check and prepare options dict."""
    # Convert match and exclude args into pattern lists
    match = opts.get("match")
    if match and type(match) is str:
        opts["match"] = [pat.strip() for pat in match.split(",")]
    elif match:
        assert type(match) is list
    else:
        opts["match"] = []

    exclude = opts.get("exclude")
    if exclude and type(exclude) is str:
        opts["exclude"] = [pat.strip() for pat in exclude.split(",")]
    elif exclude:
        assert type(exclude) is list
    else:
        # opts["exclude"] = DEFAULT_OMIT
        opts["exclude"] = []
    # print(match, exclude, opts)


def match_path(entry, opts):
    """Return True if `path` matches `match` and `exclude` options."""
    if entry.name in ALWAYS_OMIT:
        return False
    # TODO: currently we use fnmatch syntax and match against names.
    # We also might allow glob syntax and match against the whole relative path instead
    # path = entry.get_rel_path()
    path = entry.name
    ok = True
    match = opts.get("match")
    exclude = opts.get("exclude")
    if entry.is_file() and match:
        assert type(match) is list
        ok = False
        for pat in match:
            if fnmatch.fnmatch(path, pat):
                ok = True
                break
    if ok and exclude:
        assert type(exclude) is list
        for pat in exclude:
            if fnmatch.fnmatch(path, pat):
                ok = False
                break
    # write("match", ok, entry)
    return ok


# ===============================================================================
# BaseSynchronizer
# ===============================================================================
class BaseSynchronizer:
    """Synchronizes two target instances in dry_run mode (also base class for other synchronizers)."""

    _resolve_shortcuts = {"l": "local", "r": "remote", "s": "skip"}

    def __init__(self, local, remote, options):
        self.local = local
        self.remote = remote
        # TODO: check for self-including paths

        self.options = options or {}
        process_options(self.options)

        self.verbose = self.options.get("verbose", 3)
        self.dry_run = self.options.get("dry_run", False)
        #         self.local.synchronizer = self
        #         self.local.peer = remote
        #         self.remote.synchronizer = self
        #         self.remote.peer = local
        #         if self.dry_run:
        #             self.local.readonly = True
        #             self.local.dry_run = True
        #             self.remote.readonly = True
        #             self.remote.dry_run = True
        #: bool: True if this synchronizer is used by a command line script (e.g. pyftpsync.exe)
        self.is_script = None
        #: str: Conflict resolution strategy
        self.resolve_all = None

        self._stats = {
            "bytes_written": 0,
            "conflict_files": 0,
            "conflict_files_skipped": 0,
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
            "interactive_ask": 0,
            "local_dirs": 0,
            "local_files": 0,
            "meta_bytes_read": 0,
            "meta_bytes_written": 0,
            "remote_dirs": 0,
            "remote_files": 0,
            "result_code": None,
            "upload_bytes_written": 0,
            "upload_files_written": 0,
        }

    #         if not local.connected:
    #             local.open()
    #         if not remote.connected:
    #             remote.open()

    def __del__(self):
        self.close()

    def get_info_strings(self):
        raise NotImplementedError

    def close(self):
        if self.local.connected:
            self.local.close()
        if self.remote.connected:
            self.remote.close()

    def get_stats(self):
        return self._stats

    def _inc_stat(self, name, ofs=1):
        self._stats[name] = self._stats.get(name, 0) + ofs

    def _match(self, entry):
        return match_path(entry, self.options)

    def run(self):
        start = time.time()

        info_strings = self.get_info_strings()
        if self.verbose >= 3:
            write(
                "{} {}\n{:>20} {}".format(
                    info_strings[0].capitalize(),
                    self.local.get_base_name(),
                    info_strings[1],
                    self.remote.get_base_name(),
                )
            )
            write(
                "Encoding local: {}, remote: {}".format(
                    self.local.encoding, self.remote.encoding
                )
            )

        try:
            self.local.synchronizer = self.remote.synchronizer = self
            self.local.peer = self.remote
            self.remote.peer = self.local

            if self.dry_run:
                self.local.readonly = True
                self.local.dry_run = True
                self.remote.readonly = True
                self.remote.dry_run = True

            if not self.local.connected:
                self.local.open()
            if not self.remote.connected:
                self.remote.open()

            res = self._sync_dir()
        finally:
            self.local.synchronizer = self.remote.synchronizer = None
            self.local.peer = self.remote.peer = None
            self.close()

        stats = self._stats
        stats["elap_secs"] = time.time() - start
        stats["elap_str"] = "%0.2f sec" % stats["elap_secs"]

        def _add(rate, size, time):
            if stats.get(time) and stats.get(size):
                stats[rate] = "%0.2f kB/sec" % (0.001 * stats[size] / stats[time])

        _add("upload_rate_str", "upload_bytes_written", "upload_write_time")
        _add("download_rate_str", "download_bytes_written", "download_write_time")
        return res

    def _compare_file(self, local, remote):
        """Byte compare two files (early out on first difference)."""
        assert isinstance(local, FileEntry) and isinstance(remote, FileEntry)

        if not local or not remote:
            write("    Files cannot be compared ({} != {}).".format(local, remote))
            return False
        elif local.size != remote.size:
            write(
                "    Files are different (size {:,d} != {:,d}).".format(
                    local.size, remote.size
                )
            )
            return False

        with local.target.open_readable(
            local.name
        ) as fp_src, remote.target.open_readable(remote.name) as fp_dest:
            res, ofs = byte_compare(fp_src, fp_dest)

        if not res:
            write("    Files are different at offset {:,d}.".format(ofs))
        else:
            write("    Files are equal.")
        return res

    def _copy_file(self, src, dest, file_entry):
        # TODO: safe replace:
        # 1. remove temp file
        # 2. copy to target.temp
        # 3. use loggingFile for feedback
        # 4. rename target.temp
        # write("_copy_file(%s, %s --> %s)" % (file_entry, src, dest))
        assert isinstance(file_entry, FileEntry)
        self._inc_stat("files_written")
        self._inc_stat("entries_touched")
        is_upload = dest is self.remote
        if is_upload:
            self._inc_stat("upload_files_written")
        else:
            self._inc_stat("download_files_written")
        self._tick()
        if self.dry_run:
            return self._dry_run_action(
                "copy file ({}, {} --> {})".format(file_entry, src, dest)
            )
        elif dest.readonly:
            raise RuntimeError("target is read-only: {}".format(dest))

        start = time.time()

        def __block_written(data):
            # write("__block_written() {} bytes".format(len(data)))
            self._inc_stat("bytes_written", len(data))
            if is_upload:
                self._inc_stat("upload_bytes_written", len(data))
            else:
                self._inc_stat("download_bytes_written", len(data))

        if isinstance(src, FTPTarget) and not isinstance(dest, FTPTarget):
            # Copy FTP to File:
            # FTPTarget.open_readable() would read everything into a temporary buffer
            # before we can start writing.
            # It is more efficient to let FTPTarget write in the retrbinary() callbacks.
            # (Note that copying FTP to FTP would require a temp buffer anyway,
            # so we handle this in the default branch below.)
            with dest.open_writable(file_entry.name) as fp_dest:
                src.copy_to_file(file_entry.name, fp_dest, callback=__block_written)
        else:
            with src.open_readable(file_entry.name) as fp_src:
                dest.write_file(file_entry.name, fp_src, callback=__block_written)

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
        # write("_copy_recursive(%s, %s --> %s)" % (dir_entry, src, dest))
        assert isinstance(dir_entry, DirectoryEntry)
        self._inc_stat("entries_touched")
        self._inc_stat("dirs_created")
        self._tick()
        if self.dry_run:
            return self._dry_run_action(
                "copy directory ({}, {} --> {})".format(dir_entry, src, dest)
            )
        elif dest.readonly:
            raise RuntimeError("target is read-only: {}".format(dest))

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
        # write("_remove_file(%s)" % (file_entry, ))
        assert isinstance(file_entry, FileEntry)
        self._inc_stat("entries_touched")
        self._inc_stat("files_deleted")
        if self.dry_run:
            return self._dry_run_action("delete file ({})".format(file_entry))
        elif file_entry.target.readonly:
            raise RuntimeError("target is read-only: {}".format(file_entry.target))
        file_entry.target.remove_file(file_entry.name)
        file_entry.target.remove_sync_info(file_entry.name)

    def _remove_dir(self, dir_entry):
        # TODO: honor backup
        assert isinstance(dir_entry, DirectoryEntry)
        self._inc_stat("entries_touched")
        self._inc_stat("dirs_deleted")
        if self.dry_run:
            return self._dry_run_action("delete directory ({})".format(dir_entry))
        elif dir_entry.target.readonly:
            raise RuntimeError("target is read-only: {}".format(dir_entry.target))
        dir_entry.target.rmdir(dir_entry.name)
        dir_entry.target.remove_sync_info(dir_entry.name)

    def _log_action(self, action, status, symbol, entry, min_level=3):
        if self.verbose < min_level:
            return

        if len(symbol) > 1 and symbol[0] in (">", "<"):
            symbol = (
                " " + symbol
            )  # make sure direction characters are aligned at 2nd column

        color = ""
        final = ""
        if not self.options.get("no_color"):
            # CM = self.COLOR_MAP
            # color = CM.get((action, status),
            #                CM.get(("*", status),
            #                       CM.get((action, "*"),
            #                              "")))
            if action in ("copy", "restore"):
                if "<" in symbol:
                    if status == "new":
                        color = ansi_code("Fore.GREEN") + ansi_code("Style.BRIGHT")
                    else:
                        color = ansi_code("Fore.GREEN")
                else:
                    if status == "new":
                        color = ansi_code("Fore.CYAN") + ansi_code("Style.BRIGHT")
                    else:
                        color = ansi_code("Fore.CYAN")
            elif action == "delete":
                color = ansi_code("Fore.RED")
            elif status == "conflict":
                color = ansi_code("Fore.LIGHTRED_EX")
            elif action == "skip" or status == "equal" or status == "visit":
                color = ansi_code("Fore.LIGHTBLACK_EX")

            final = ansi_code("Style.RESET_ALL")

        if colorama:
            # Clear line"ESC [ mode K" mode 0:to-right, 2:all
            final += colorama.ansi.clear_line(0)
        else:
            final += " " * 10
        prefix = ""
        if self.dry_run:
            prefix = DRY_RUN_PREFIX

        if action and status:
            tag = ("{} {}".format(action, status)).upper()
        else:
            assert status
            tag = ("{}".format(status)).upper()

        name = entry.get_rel_path()
        if entry.is_dir():
            name = "[{}]".format(name)

        write("{}{}{:<16} {:^3} {}{}".format(prefix, color, tag, symbol, name, final))

    def _tick(self):
        """Write progress info and move cursor to beginning of line."""
        if (self.verbose >= 3 and not IS_REDIRECTED) or self.options.get("progress"):
            stats = self.get_stats()
            prefix = DRY_RUN_PREFIX if self.dry_run else ""
            sys.stdout.write(
                "{}Touched {}/{} entries in {} directories...\r".format(
                    prefix,
                    stats["entries_touched"],
                    stats["entries_seen"],
                    stats["local_dirs"],
                )
            )
        sys.stdout.flush()
        return

    def _dry_run_action(self, action):
        """"Called in dry-run mode after call to _log_action() and before exiting function."""
        # write("dry-run", action)
        return

    def _test_match_or_print(self, entry):
        """Return True if entry matches filter. Otherwise print 'skip' and return False."""
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

    def _sync_dir(self):
        """Traverse the local folder structure and remote peers.

        This is the core algorithm that generates calls to self.sync_XXX()
        handler methods.
        _sync_dir() is called by self.run().
        """
        local_entries = self.local.get_dir()
        # Convert into a dict {name: FileEntry, ...}
        local_entry_map = dict(map(lambda e: (e.name, e), local_entries))

        remote_entries = self.remote.get_dir()
        # Convert into a dict {name: FileEntry, ...}
        remote_entry_map = dict(map(lambda e: (e.name, e), remote_entries))

        entry_pair_list = []

        # 1. Loop over all local files and classify the relationship to the
        #    peer entries.
        for local_entry in local_entries:
            if isinstance(local_entry, DirectoryEntry):
                self._inc_stat("local_dirs")
            else:
                self._inc_stat("local_files")

            if not self._before_sync(local_entry):
                # TODO: currently, if a file is skipped, it will not be
                # considered for deletion on the peer target
                continue
            # TODO: case insensitive?
            # We should use os.path.normcase() to convert to lowercase on windows
            # (i.e. if the FTP server is based on Windows)
            remote_entry = remote_entry_map.get(local_entry.name)

            entry_pair = EntryPair(local_entry, remote_entry)
            entry_pair_list.append(entry_pair)

            # TODO: renaming could be triggered, if we find an existing
            # entry.unique with a different entry.name

        # 2. Collect all remote entries that do NOT exist on the local target.
        for remote_entry in remote_entries:
            if isinstance(remote_entry, DirectoryEntry):
                self._inc_stat("remote_dirs")
            else:
                self._inc_stat("remote_files")

            if not self._before_sync(remote_entry):
                continue

            if remote_entry.name not in local_entry_map:
                entry_pair = EntryPair(None, remote_entry)
                entry_pair_list.append(entry_pair)
                # print("NOT IN LOCAL")
                # print(remote_entry.name)
                # print(self.remote.get_id())
                # print(local_entry_map.keys())
                # print(self.local.cur_dir_meta.peer_sync.get(self.remote.get_id()))

        # 3. Classify all entries and pairs.
        #    We pass the additional meta data here
        peer_dir_meta = self.local.cur_dir_meta.peer_sync.get(self.remote.get_id())

        for pair in entry_pair_list:
            pair.classify(peer_dir_meta)

        # 4. Perform (or schedule) resulting file operations
        for pair in entry_pair_list:

            # print(pair)

            # Let synchronizer modify the default operation (e.g. apply `--force` option)
            hook_result = self.re_classify_pair(pair)

            # Let synchronizer implement special handling of unmatched entries
            # (e.g. `--delete_unmatched`)
            if not self._match(pair.any_entry):
                self.on_mismatch(pair)
                # ... do not call operation handler...
            elif hook_result is not False:
                handler = getattr(self, "on_" + pair.operation, None)
                # print(handler)
                if handler:
                    try:
                        res = handler(pair)
                    except Exception as e:
                        if self.on_error(e, pair) is not True:
                            raise
                else:
                    # write("NO HANDLER")
                    raise NotImplementedError("No handler for {}".format(pair))

            if pair.is_conflict():
                self._inc_stat("conflict_files")

        # 5. Let the target provider write its meta data for the files in the
        #    current directory.
        self.local.flush_meta()
        self.remote.flush_meta()

        # 6. Finally visit all local sub-directories recursively that also
        #    exist on the remote target.
        for local_dir in local_entries:
            # write("local_dir(%s, %s)" % (local_dir, local_dir))
            if not local_dir.is_dir():
                continue
            elif not self._before_sync(local_dir):
                continue

            remote_dir = remote_entry_map.get(local_dir.name)
            if remote_dir:
                # write("sync_equal_dir(%s, %s)" % (local_dir, remote_dir))
                # self._log_call("sync_equal_dir(%s, %s)" % (local_dir, remote_dir))
                # res = self.sync_equal_dir(local_dir, remote_dir)
                # res = self.on_equal(local_dir, remote_dir)
                if res is not False:
                    self.local.cwd(local_dir.name)
                    self.remote.cwd(local_dir.name)
                    self._sync_dir()
                    self.local.cwd("..")
                    self.remote.cwd("..")

        return True

    def re_classify_pair(self, pair):
        """Allow derrived classes to override default classification and operation.

        Returns:
            False to prevent default operation.
        """
        return True

    def on_error(self, e, pair):
        """Called for pairs that don't match `match` and `exclude` filters."""
        RED = ansi_code("Fore.LIGHTRED_EX")
        R = ansi_code("Style.RESET_ALL")
        # any_entry = pair.any_entry
        write((RED + "ERROR: {}\n    {}" + R).format(e, pair))
        # Return True to ignore this error (instead of raising and terminating the app)
        # if "[Errno 92] Illegal byte sequence" in "{}".format(e) and compat.PY2:
        #     write(RED + "This _may_ be solved by using Python 3." + R)
        #     # return True
        return False

    def on_mismatch(self, pair):
        """Called for pairs that don't match `match` and `exclude` filters."""
        self._log_action("skip", "mismatch", "?", pair.any_entry, min_level=4)

    def on_equal(self, pair):
        """Called for (unmodified, unmodified) pairs."""
        self._log_action("", "equal", "=", pair.local, min_level=4)

    def on_copy_local(self, pair):
        """Called when the local resource should be copied to remote."""
        status = pair.remote_classification
        self._log_action("copy", status, ">", pair.local)

    def on_copy_remote(self, pair):
        """Called when the remote resource should be copied to local."""
        status = pair.local_classification
        self._log_action("copy", status, "<", pair.remote)

    def on_delete_local(self, pair):
        """Called when the local resource should be deleted."""
        self._log_action("", "modified", "X< ", pair.local)

    def on_delete_remote(self, pair):
        """Called when the remote resource should be deleted."""
        self._log_action("", "modified", " >X", pair.remote)

    def on_need_compare(self, pair):
        """Re-classify pair based on file attributes and options."""
        self._log_action("", "different", "?", pair.local, min_level=2)

    def on_conflict(self, pair):
        """Called when resources have been modified on local *and* remote.

        Returns:
            False to prevent visiting of children (if pair is a directory)
        """
        self._log_action("skip", "conflict", "!", pair.local, min_level=2)


# ===============================================================================
# BiDirSynchronizer
# ===============================================================================
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

    def _print_pair_diff(self, pair):
        RED = ansi_code("Fore.LIGHTRED_EX")
        # M = ansi_code("Style.BRIGHT") + ansi_code("Style.UNDERLINE")
        R = ansi_code("Style.RESET_ALL")

        any_entry = pair.any_entry

        has_meta = any_entry.get_sync_info("m") is not None

        # write("pair", pair)
        # print("pair.local", pair.local)
        # print("pair.remote", pair.remote)

        write(
            (
                VT_ERASE_LINE
                + RED
                + "CONFLICT: {!r} was modified on both targets since last sync ({})."
                + R
            ).format(any_entry.get_rel_path(), _ts(any_entry.get_sync_info("u")))
        )
        if has_meta:
            write(
                "    Original modification time: {}, size: {:,d} bytes.".format(
                    _ts(any_entry.get_sync_info("m")), any_entry.get_sync_info("s")
                )
            )
        else:
            write("    (No meta data available.)")

        write("    Local:  {}".format(pair.local.as_string() if pair.local else "n.a."))
        write(
            "    Remote: {}".format(
                pair.remote.as_string(pair.local) if pair.remote else "n.a."
            )
        )

    def _interactive_resolve(self, pair):
        """Return 'local', 'remote', or 'skip' to use local, remote resource or skip."""
        if self.resolve_all:
            # A resolution strategy was selected using Shift+MODE
            resolve = self.resolve_all
        else:
            # A resolution strategy was configured
            resolve = self.options.get("resolve", "skip")

        if resolve in ("new", "old") and pair.is_same_time():
            # We cannot apply this resolution: force an alternative
            print("Cannot resolve using '{}' strategy: {}".format(resolve, pair))
            resolve = "ask" if self.is_script else "skip"

        if resolve == "ask" or self.verbose >= 5:
            self._print_pair_diff(pair)

        if resolve in ("local", "remote", "old", "new", "skip"):
            # self.resolve_all = resolve
            return resolve

        # RED = ansi_code("Fore.LIGHTRED_EX")
        M = ansi_code("Style.BRIGHT") + ansi_code("Style.UNDERLINE")
        R = ansi_code("Style.RESET_ALL")

        self._inc_stat("interactive_ask")

        while True:
            prompt = (
                "Use "
                + M
                + "L"
                + R
                + "ocal, "
                + M
                + "R"
                + R
                + "emote, "
                + M
                + "O"
                + R
                + "lder, "
                + M
                + "N"
                + R
                + "ewer, "
                + M
                + "S"
                + R
                + "kip, "
                + M
                + "B"
                + R
                + "inary compare, "
                + M
                + "H"
                + R
                + "elp ? "
            )

            r = input(prompt).strip()

            if r in ("h", "H", "?"):
                print("The following keys are supported:")
                print("  'b': Binary compare")
                print("  'n': Use newer file")
                print("  'o': Use older file")
                print("  'l': Use local file")
                print("  'r': Use remote file")
                print("  's': Skip this file (leave both targets unchanged)")
                print(
                    "Hold Shift (upper case letters) to apply choice for all "
                    "remaining conflicts."
                )
                print("Hit Ctrl+C to abort.")
                self._print_pair_diff(pair)
                continue

            elif r in ("b", "B"):
                # TODO: we could (offer to) set both mtimes to the same value
                # if files are identical
                self._compare_file(pair.local, pair.remote)
                # self._print_pair_diff(pair)
                continue

            elif r in ("o", "O", "n", "N") and pair.is_same_time():
                # Ignore 'old' or 'new' selection if times are the same
                print("Files have identical modification times.")
                continue

            elif r in ("L", "R", "O", "N", "S"):
                r = self._resolve_shortcuts[r.lower()]
                self.resolve_all = r
                break

            elif r in ("l", "r", "o", "n", "s"):
                r = self._resolve_shortcuts[r]
                break

        return r

    def run(self):
        # Don't override setting by derived up/downloader
        res = super(BiDirSynchronizer, self).run()
        return res

    def on_mismatch(self, pair):
        """Called for pairs that don't match `match` and `exclude` filters."""
        self._log_action("skip", "mismatch", "?", pair.any_entry, min_level=4)

    def on_equal(self, pair):
        self._log_action("", "equal", "=", pair.local, min_level=4)

    def on_copy_local(self, pair):
        local_entry = pair.local
        if self._test_match_or_print(local_entry):
            self._log_action("copy", pair.local_classification, ">", local_entry)
            if pair.is_dir:
                self._copy_recursive(self.local, self.remote, local_entry)
            else:
                self._copy_file(self.local, self.remote, local_entry)

    def on_copy_remote(self, pair):
        remote_entry = pair.remote
        if self._test_match_or_print(remote_entry):
            self._log_action("copy", pair.remote_classification, "<", remote_entry)
            if pair.is_dir:
                self._copy_recursive(self.remote, self.local, remote_entry)
            else:
                self._copy_file(self.remote, self.local, remote_entry)

    def on_delete_local(self, pair):
        self._log_action("delete", "missing", "X< ", pair.local)
        # self._log_action("delete", pair.local_classification, "X< ", pair.local)
        if pair.is_dir:
            self._remove_dir(pair.local)
        else:
            self._remove_file(pair.local)

    def on_delete_remote(self, pair):
        self._log_action("delete", "missing", " >X", pair.remote)
        # self._log_action("delete", pair.remote_classification, " >X", pair.remote)
        if pair.is_dir:
            self._remove_dir(pair.remote)
        else:
            self._remove_file(pair.remote)

    def on_need_compare(self, pair):
        """Re-classify pair based on file attributes and options."""
        # print("on_need_compare", pair)
        # If no metadata is available, we could only classify file entries as
        # 'existing'.
        # Now we use peer information to improve this classification.
        c_pair = (pair.local_classification, pair.remote_classification)

        org_pair = c_pair
        org_operation = pair.operation

        # print("need_compare", pair)

        if pair.is_dir:
            # For directores, we cannot compare existing peer entries.
            # Instead, we simply log (and traverse the children later).
            pair.local_classification = pair.remote_classification = "existing"
            pair.operation = "equal"
            self._log_action("", "visit", "?", pair.local, min_level=4)
            # self._log_action("", "equal", "=", pair.local, min_level=4)
            return

        elif c_pair == ("existing", "existing"):
            # Naive classification derived from file time and size
            time_cmp = eps_compare(
                pair.local.mtime, pair.remote.mtime, FileEntry.EPS_TIME
            )
            if time_cmp < 0:
                c_pair = ("unmodified", "modified")  # remote is newer
            elif time_cmp > 0:
                c_pair = ("modified", "unmodified")  # local is newer
            elif pair.local.size == pair.remote.size:
                c_pair = ("unmodified", "unmodified")  # equal
            else:
                c_pair = ("modified", "modified")  # conflict!

        elif c_pair == ("new", "new"):
            # Naive classification derived from file time and size
            time_cmp = eps_compare(
                pair.local.mtime, pair.remote.mtime, FileEntry.EPS_TIME
            )
            if time_cmp == 0 and pair.local.size == pair.remote.size:
                c_pair = ("unmodified", "unmodified")  # equal
            else:
                c_pair = ("modified", "modified")  # conflict!

        # elif c_pair == ("unmodified", "unmodified"):

        pair.local_classification = c_pair[0]
        pair.remote_classification = c_pair[1]

        pair.operation = operation_map.get(c_pair)
        # print("on_need_compare {} => {}".format(org_pair, pair))
        if not pair.operation:
            raise RuntimeError(
                "Undefined operation for pair classification {}".format(c_pair)
            )
        elif pair.operation == org_operation:
            raise RuntimeError("Could not re-classify  {}".format(org_pair))

        handler = getattr(self, "on_" + pair.operation, None)
        res = handler(pair)
        #         self._log_action("", "different", "?", pair.local, min_level=2)
        return res

    def on_conflict(self, pair):
        """Return False to prevent visiting of children."""
        # self._log_action("skip", "conflict", "!", pair.local, min_level=2)
        # print("on_conflict", pair)
        any_entry = pair.any_entry
        if not self._test_match_or_print(any_entry):
            return

        resolve = self._interactive_resolve(pair)

        if resolve == "skip":
            self._log_action("skip", "conflict", "*?*", any_entry)
            self._inc_stat("conflict_files_skipped")
            return

        if pair.local and pair.remote:
            assert pair.local.is_file()
            is_newer = pair.local > pair.remote
            if (
                resolve == "local"
                or (is_newer and resolve == "new")
                or (not is_newer and resolve == "old")
            ):
                self._log_action("copy", "conflict", "*>*", pair.local)
                self._copy_file(self.local, self.remote, pair.local)
            elif (
                resolve == "remote"
                or (is_newer and resolve == "old")
                or (not is_newer and resolve == "new")
            ):
                self._log_action("copy", "conflict", "*<*", pair.local)
                self._copy_file(self.remote, self.local, pair.remote)
            else:
                raise NotImplementedError
        elif pair.local:
            assert pair.local.is_file()
            if resolve == "local":
                self._log_action("restore", "conflict", "*>x", pair.local)
                self._copy_file(self.local, self.remote, pair.local)
            elif resolve == "remote":
                self._log_action("delete", "conflict", "*<x", pair.local)
                self._remove_file(pair.local)
            else:
                raise NotImplementedError
        else:
            assert pair.remote.is_file()
            if resolve == "local":
                self._log_action("delete", "conflict", "x>*", pair.remote)
                self._remove_file(pair.remote)
            elif resolve == "remote":
                self._log_action("restore", "conflict", "x<*", pair.remote)
                self._copy_file(self.remote, self.local, pair.remote)
            else:
                raise NotImplementedError
        return


# ===============================================================================
# UploadSynchronizer
# ===============================================================================


class UploadSynchronizer(BiDirSynchronizer):
    def __init__(self, local, remote, options):
        super(UploadSynchronizer, self).__init__(local, remote, options)

    #         local.readonly = True

    def get_info_strings(self):
        return ("upload", "to")

    def re_classify_pair(self, pair):
        force = self.options.get("force")
        # delete = self.options.get("delete")
        is_file = not pair.is_dir

        classification = (pair.local_classification, pair.remote_classification)

        # print("re_classify_pair", pair)
        if classification == ("missing", "new"):
            assert pair.operation == "copy_remote"
            pair.override_operation("delete_remote", "restore")

        if force:
            if is_file and classification == ("new", "new"):
                pair.override_operation("copy_local", "force")
            elif is_file and classification == ("modified", "modified"):
                pair.override_operation("copy_local", "force")
            elif is_file and classification == ("unmodified", "modified"):
                pair.override_operation("copy_local", "restore")
            elif is_file and classification == ("existing", "existing"):
                pair.override_operation("copy_local", "force")
            elif classification == ("unmodified", "deleted"):
                pair.override_operation("copy_local", "restore")

        return True

    def _interactive_resolve(self, pair):
        """Return 'local', 'remote', or 'skip' to use local, remote resource or skip."""
        # RED = ansi_code("Fore.LIGHTRED_EX")
        M = ansi_code("Style.BRIGHT") + ansi_code("Style.UNDERLINE")
        R = ansi_code("Style.RESET_ALL")

        resolve = self.options.get("resolve", "skip")
        assert resolve in ("local", "ask", "skip")

        if self.resolve_all:
            if self.verbose >= 5:
                self._print_pair_diff(pair)
            return self.resolve_all

        if resolve == "ask" or self.verbose >= 5:
            self._print_pair_diff(pair)

        if resolve in ("local", "skip"):
            # self.resolve_all = resolve
            return resolve

        self._inc_stat("interactive_ask")

        while True:
            prompt = (
                "Use "
                + M
                + "L"
                + R
                + "ocal, "
                + M
                + "S"
                + R
                + "kip, "
                + M
                + "B"
                + R
                + "inary compare, "
                + M
                + "H"
                + R
                + "elp ? "
            )

            r = input(prompt).strip()

            if r in ("h", "H", "?"):
                print("The following keys are supported:")
                print("  'b': Binary compare")
                print("  'l': Upload local file")
                print("  's': Skip this file (leave both targets unchanged)")
                print(
                    "Hold Shift (upper case letters) to apply choice for all "
                    "remaining conflicts."
                )
                print("Hit Ctrl+C to abort.")
                continue
            elif r in ("B", "b"):
                self._compare_file(pair.local, pair.remote)
                continue
            elif r in ("L", "S"):
                r = self._resolve_shortcuts[r.lower()]
                self.resolve_all = r
                break
            elif r in ("l", "s"):
                r = self._resolve_shortcuts[r]
                break

        return r

    def run(self):
        self.local.readonly = True
        self.remote.readonly = False
        res = super(UploadSynchronizer, self).run()
        return res

    def on_mismatch(self, pair):
        """Called for pairs that don't match `match` and `exclude` filters.

        If --delete-unmatched is on, remove the remote resource.
        """
        remote_entry = pair.remote
        if self.options.get("delete_unmatched") and remote_entry:
            self._log_action("delete", "unmatched", ">", remote_entry)
            if remote_entry.is_dir():
                self._remove_dir(remote_entry)
            else:
                self._remove_file(remote_entry)
        else:
            self._log_action("skip", "unmatched", "-", pair.any_entry, min_level=4)

    # def on_equal(self, pair):
    #     self._log_action("", "equal", "=", pair.local, min_level=4)

    def on_copy_remote(self, pair):
        # Uploads does not modify local target
        # status = pair.local.classification if pair.local else "missing"
        self._log_action("skip", "download", "<", pair.remote)

    def on_delete_local(self, pair):
        # Uploads does not modify local target
        self._log_action("skip", "local del.", "X< ", pair.local)

    def on_delete_remote(self, pair):
        # Upload does not delete unless --delete was given
        if not self.options.get("delete"):
            self._log_action("skip", "remote del.", " >X", pair.remote)
            return
        return super(UploadSynchronizer, self).on_delete_remote(pair)

    # def on_need_compare(self, pair):
    #     self._log_action("", "different", "?", pair.local, min_level=2)

    # def on_conflict(self, pair):
    #     """Return False to prevent visiting of children"""
    #     self._log_action("skip", "conflict", "!", pair.local, min_level=2)


# ===============================================================================
# DownloadSynchronizer
# ===============================================================================


class DownloadSynchronizer(BiDirSynchronizer):
    """"""

    def __init__(self, local, remote, options):
        super(DownloadSynchronizer, self).__init__(local, remote, options)

    #         remote.readonly = True

    def get_info_strings(self):
        return ("download to", "from")

    def re_classify_pair(self, pair):
        force = self.options.get("force")
        # delete = self.options.get("delete")
        is_file = not pair.is_dir

        classification = (pair.local_classification, pair.remote_classification)

        # write("re_classify_pair: {}".format(pair))
        if classification == ("new", "missing"):
            assert pair.operation == "copy_local"
            pair.override_operation("delete_local", "restore")

        if force:
            if is_file and classification == ("new", "new"):
                pair.override_operation("copy_remote", "forced")
            elif is_file and classification == ("modified", "unmodified"):
                pair.override_operation("copy_remote", "restore")
            elif is_file and classification == ("modified", "modified"):
                pair.override_operation("copy_remote", "force")
            elif is_file and classification == ("existing", "existing"):
                pair.override_operation("copy_remote", "force")
            elif classification == ("deleted", "unmodified"):
                pair.override_operation("copy_remote", "restore")

        return True

    def _interactive_resolve(self, pair):
        """Return 'local', 'remote', or 'skip' to use local, remote resource or skip."""
        if self.resolve_all:
            if self.verbose >= 5:
                self._print_pair_diff(pair)
            return self.resolve_all

        resolve = self.options.get("resolve", "skip")
        assert resolve in ("remote", "ask", "skip")

        if resolve == "ask" or self.verbose >= 5:
            self._print_pair_diff(pair)

        if resolve in ("remote", "skip"):
            # self.resolve_all = resolve
            return resolve

        # RED = ansi_code("Fore.LIGHTRED_EX")
        M = ansi_code("Style.BRIGHT") + ansi_code("Style.UNDERLINE")
        R = ansi_code("Style.RESET_ALL")

        # self._print_pair_diff(pair)

        self._inc_stat("interactive_ask")

        while True:
            prompt = (
                "Use "
                + M
                + "R"
                + R
                + "emote, "
                + M
                + "S"
                + R
                + "kip, "
                + M
                + "B"
                + R
                + "inary compare, "
                + M
                + "H"
                + R
                + "elp? "
            )

            r = input(prompt).strip()
            if r in ("h", "H", "?"):
                print("The following keys are supported:")
                print("  'b': Binary compare")
                print("  'r': Download remote file")
                print("  's': Skip this file (leave both targets unchanged)")
                print(
                    "Hold Shift (upper case letters) to apply choice for all "
                    "remaining conflicts."
                )
                print("Hit Ctrl+C to abort.")
                continue
            elif r in ("B", "b"):
                self._compare_file(pair.local, pair.remote)
                continue
            elif r in ("R", "S"):
                r = self._resolve_shortcuts[r.lower()]
                self.resolve_all = r
                break
            elif r in ("r", "s"):
                r = self._resolve_shortcuts[r]
                break

        return r

    def run(self):
        self.local.readonly = False
        self.remote.readonly = True
        res = super(DownloadSynchronizer, self).run()
        return res

    def on_mismatch(self, pair):
        """Called for pairs that don't match `match` and `exclude` filters.

        If --delete-unmatched is on, remove the remote resource.
        """
        local_entry = pair.local
        if self.options.get("delete_unmatched") and local_entry:
            self._log_action("delete", "unmatched", "<", local_entry)
            if local_entry.is_dir():
                self._remove_dir(local_entry)
            else:
                self._remove_file(local_entry)
        else:
            self._log_action("skip", "unmatched", "-", pair.any_entry, min_level=4)

    # def on_equal(self, pair):
    #     self._log_action("", "equal", "=", pair.local, min_level=4)
    #     # self._check_del_unmatched(local_file)

    def on_copy_local(self, pair):
        # Download does not modify remote target
        # status = pair.remote.classification if pair.remote else "missing"
        self._log_action("skip", "upload", ">", pair.local)

    def on_delete_local(self, pair):
        # Download does not delete unless --delete was given
        if not self.options.get("delete"):
            self._log_action("skip", "local del.", "X< ", pair.local)
            return
        return super(DownloadSynchronizer, self).on_delete_local(pair)

    def on_delete_remote(self, pair):
        # Download does not modify remote target
        self._log_action("skip", "remote del.", " >X", pair.remote)

    # def on_need_compare(self, pair):
    #     self._log_action("", "different", "?", pair.local, min_level=2)
    #
    # def on_conflict(self, pair):
    #     """Return False to prevent visiting of children"""
    #     self._log_action("skip", "conflict", "!", pair.local, min_level=2)

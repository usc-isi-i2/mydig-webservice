import multiprocessing
from datetime import datetime

import git

from config import config

GIT_PUSH_MSG = {64 : 'DELETED', 1024 : 'ERROR', 256 : 'FAST_FORWARD', 128 : 'FORCED_UPDATE',
                2 : 'NEW_HEAD', 1 : 'NEW_TAG', 4 : 'NO_MATCH', 8 : 'REJECTED', 32 : 'REMOTE_FAILURE',
                16 : 'REMOTE_REJECTED', 512 : 'UP_TO_DATE', 1032 : 'REMOTE CONTAINS WORK NOT PRESENT IN LOCAL'}

GIT_PULL_MSG = {128: "ERROR", 64: "FAST_FORWARD", 32: "FORCED_UPDATE", 4: "HEAD_UPTODATE",
                2: "NEW_HEAD", 1: "NEW_TAG", 16: "REJECTED", 8: "TAG_UPDATE"}


if config['repo']['git']['enable_sync']:
    repo = git.Repo(config['repo']['local_path'])
    # repo.git.custom_environment(GIT_SSH_COMMAND='ssh -i ' + config['repo']['git']['ssh_key_file_path'])
    remote_obj = git.Remote(repo, 'origin')
    remote_obj.set_url(config['repo']['git']['remote_url'])


def pull():
    def _pull():
        pullinfo = remote_obj.pull()
        flag = pullinfo[0].flags
        # return flag
        return GIT_PULL_MSG.get(flag, 'Unknown: ' + str(flag))

    if not config['repo']['git']['enable_sync']:
        return

    # sync
    ret = _pull()
    return ret


def commit(files=['*'], message=str(datetime.now())):
    def _commit(files, message):
        # print repo.untracked_files
        repo.index.add(files)
        repo.index.commit(message)

    if not config['repo']['git']['enable_sync']:
        return

    # async
    if len(files) == 0:
        return
    p = multiprocessing.Process(target=_commit, args=(files, message,))
    p.start()
    return


def push():
    def _push():
        pushinfo = remote_obj.push()
        flag = pushinfo[0].flags
        # return flag
        print GIT_PUSH_MSG.get(flag, 'Unknown: ' + str(flag))

    if not config['repo']['git']['enable_sync']:
        return

    # async
    p = multiprocessing.Process(target=_push)
    p.start()
    return


import compiling_cpp, status
from status import *
import func_timeout
import io
import subprocess
import os
import time

class LoadedKey:
    def __init__(self, data):
        self.data = data
        # data was structured in [[i1, o1], [i2, o2], ...]
        self.pvalue = 100 // len(self.data)

    def cmp(self, inputid, output):
        answer = self.data[inputid][1]
        response = '\n'.join([s.lstrip().rstrip() \
                              for s in output.splitlines()])
        if answer == response:
            return True
        else:
            return False

@func_timeout.func_set_timeout(1.01)
def get_output(exename, inputdat, args=[]):
    os.chdir(os.path.dirname(__file__))
    _f = open('__input__', 'a')
    _f.truncate(0)
    _f.write(inputdat)
    _f.flush()
    _f.close()
    PIPE = subprocess.PIPE
    with open('__input__', 'r') as file:
        exename = os.path.join(os.path.dirname(__file__), exename)
        s = subprocess.Popen([exename]+args, stdout=PIPE, stderr=PIPE,
                             stdin=file)
        o, e=s.communicate()
        if s.returncode == 0:
            return o.decode().replace('\r\n', '\n')
        else:
            return RTError()
    
    

def judge_proc_cpp(file, statobj: Status, updater, stop_proc, load_key,
                   spjmod=None):
    existspj = not (spjmod == None)
    _is = isinstance
    exename = compiling_cpp.compile_proc(file, statobj, updater, stop_proc)
    if exename==-1:
        return
    while not os.path.exists(os.path.join(os.path.dirname(__file__), exename)):
        time.sleep(0.1)
    time.sleep(0.7)
    # os.popen() needs this stop!
    statobj.status = Judging()
    updater(statobj)
    inputid = 0
    has_ac = False
    has_error = False
    all_rte = True
    all_tle = True
    for i, o, spj in load_key.data:
        do_cmp = True
        p = PointData()
        try:
            output = get_output(exename, i, [])
            if _is(output, RTError):
                p.kind = RTError()
                all_tle = False
                do_cmp = False
                
            if do_cmp:
                if not spj: # added this block
                    correct = load_key.cmp(inputid, output)
                    if correct:
                        all_rte = False
                        all_tle = False
                        has_ac = True
                        p.rank = load_key.pvalue
                        statobj.rank += load_key.pvalue
                        p.kind = Accepted()
                    else:
                        all_rte = False
                        all_tle = False
                        has_error = True
                        p.rank = 0
                        p.kind = WrongAnswer()
                elif existspj:
                    p.kind = SpecialJudgement()
                    p.rank = spjmod.special_judge(load_key.data[inputid][1],
                                                  output, load_key.pvalue)
                    statobj.rank += p.rank
                    if p.rank == load_key.pvalue:
                        all_rte = False
                        all_tle = False
                        has_ac = True
                        p.kind = Accepted()
                    else:
                        has_error = True
        except func_timeout.exceptions.FunctionTimedOut:
            all_rte = False
            has_error = True
            p.kind = TimeLimitExceeded()
        statobj.pointdata.append(p)
        inputid += 1
        
    if all_rte:
        statobj.kind = RTError()
    elif all_tle:
        statobj.kind = TimeLimitExceeded()
    elif not has_error and has_ac:
        statobj.kind = Accepted()
    elif not has_ac and has_error:
        statobj.kind = WrongAnswer()
    else:
        statobj.kind = PartialAccepted()
    statobj.status = Finished()
    updater(statobj)
    

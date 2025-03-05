import time

class Recorder:
    def __init__(self, score_name: str):
        self.score_ID = 0
        self.first_record = True
        self.record_status = False
        self.start_time = time.time()
        self.score_name = score_name

    def write_score(self, s: str):
        filename = self.score_name+'_'+str(self.score_ID)+'.txt'
        f = open(filename, 'a')
        f.write(s)
        f.close()
    
    def record_score(self, s: str):
        if self.record_status == True:
            if self.first_score:
                line += s
                line += '\n'
                self.first_record = False
            else:
                line = str(self.get_current_millis())
                line += '\n'
                line += s
                line += '\n'
            self.write_score(line)
            self.start_time = time.time()
            print(f'"{line}" has been recorded')
    
    def get_current_millis(self):
        return int((time.time() - self.start_time) * 1000000)
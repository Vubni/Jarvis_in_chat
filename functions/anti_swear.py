from check_swear import SwearingCheck

sch = SwearingCheck()

def is_swear(text):
    return True if sch.predict(text)[0] > 0.75 else False
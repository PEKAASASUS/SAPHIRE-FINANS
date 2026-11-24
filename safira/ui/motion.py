"""One cancellable after-chain per component/channel, no animation threads."""
import time
import tkinter as tk


class Motion:
    reduced=False
    active=set()

    def __init__(self,widget):
        self.widget=widget; self.jobs={}
        widget.bind('<Destroy>',self._destroy,add='+')

    def _destroy(self,event):
        if event.widget==self.widget: self.cancel()

    def cancel(self,channel=None):
        channels=[channel] if channel else list(self.jobs)
        for key in channels:
            handle=self.jobs.pop(key,None)
            if handle:
                try:self.widget.after_cancel(handle)
                except tk.TclError:pass
            Motion.active.discard((id(self),key))

    def animate(self,channel,duration,update,done=None):
        self.cancel(channel)
        if Motion.reduced:
            update(1)
            if done:done()
            return
        start=time.perf_counter()
        def frame():
            if not self.widget.winfo_exists(): self.cancel(channel); return
            t=1 if Motion.reduced else min(1,(time.perf_counter()-start)*1000/duration)
            update(1-(1-t)**3)
            if t<1:
                self.jobs[channel]=self.widget.after(16,frame)
                Motion.active.add((id(self),channel))
            else:
                self.jobs.pop(channel,None); Motion.active.discard((id(self),channel))
                if done:done()
        frame()

    @classmethod
    def set_reduced(cls,value):
        cls.reduced=bool(value)

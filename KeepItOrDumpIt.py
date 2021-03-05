import wx
import sys
from collections import namedtuple
from random import shuffle
import json
from time import sleep


def scale_bitmap(bitmap, width, height):
    image = bitmap.ConvertToImage()
    image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
    result = wx.Bitmap(image)
    return result


def within_aabb(x, y, xx, yy, w, h):
    return xx <= x < xx + w and yy <= y < yy + h


def remove_newlines(s):
    return ''.join(s.split('\n'))


def lin_int(a, b, t):
    return int(a * t + b * (1-t))


def adjust_font(g, txt, w, h, margin, maximal_font):
    real_w, real_h = w - margin * 2, h - margin * 2
    g.SetFont(wx.Font(maximal_font, wx.DEFAULT, wx.NORMAL, wx.NORMAL, False, 'Narkisim'))
    wid, hei = g.GetMultiLineTextExtent(txt)
    cutoffs = [k for k in range(len(txt)) if txt[k] in {' ', ',', '-', '.', ';', '\n', '/'}]
    while wid >= real_w or hei >= real_h:
        for k in cutoffs:
            s = txt[:k + (0 if txt[k] == ' ' else 1)] + '\n' + txt[k + 1:]
            wid, hei = g.GetMultiLineTextExtent(s)
            if wid < real_w and hei < real_h:
                return s

        maximal_font -= 1
        g.SetFont(wx.Font(maximal_font, wx.DEFAULT, wx.NORMAL, wx.NORMAL, False, 'Narkisim'))
        wid, hei = g.GetMultiLineTextExtent(txt)
    return txt


class MyFrame(wx.Frame):

    def __init__(self):
        wx.Frame.__init__(self, None, -1, '')
        self.Show()
        self.ShowFullScreen(True)
        self.SetDoubleBuffered(True)

        self.bg = scale_bitmap(wx.Bitmap('bg.jpg'), *self.GetSize())

        print(self.GetSize())

        self.questions = []
        self.read_questions()
        self.curq = 0
        self.innerq = 0
        self.competitors = []
        self.cur_competitor = -1
        self.load_competitors()

        self.covered = [0 for _ in range(15)]
        self.framed = [0 for _ in range(15)]

        self.frame_pen = wx.Pen(wx.RED, 3)

        self.lasso()

    def lasso(self):
        """ self.Bind() calls """
        self.Bind(wx.EVT_PAINT, self.paint_handler)
        self.Bind(wx.EVT_KEY_DOWN, self.key_handler)
        self.Bind(wx.EVT_LEFT_DOWN, self.lclick_handler)
        self.Bind(wx.EVT_ERASE_BACKGROUND, lambda e: None)  # No operation

    def paint_handler(self, e):
        g = wx.PaintDC(self)
        g.DrawBitmap(self.bg, 0, 0)

        g.SetLayoutDirection(wx.Layout_RightToLeft)

        topic, items, q1, q2 = self.questions[self.curq]['topic'], self.questions[self.curq]['items'],\
                               self.questions[self.curq]['questions'][0], self.questions[self.curq]['questions'][1]
        fandoms = self.questions[self.curq]['fandoms']
        q = (q1, q2)
        g.SetTextForeground('white')
        g.SetFont(wx.Font(44, wx.DEFAULT, wx.NORMAL, wx.NORMAL, False, 'Narkisim'))
        empty_bmp = wx.Bitmap()
        qnum = f'שאלה {self.curq}-{self.innerq + 1}: '
        title = 'נושא: ' + topic + '\n' + qnum + q[self.innerq]
        while '  ' in title:
            title = title.replace('  ', ' ')
        w, h = g.GetMultiLineTextExtent(title)
        cur_font = 44
        while w > 1000 or h > 214:
            cur_font -= 1
            g.SetFont(wx.Font(cur_font, wx.DEFAULT, wx.NORMAL, wx.NORMAL, False, 'Narkisim'))
            w, h = g.GetMultiLineTextExtent(title)
        g.DrawLabel(title, empty_bmp, wx.Rect(50, 50, 1000, 214),
                    alignment=wx.ALIGN_CENTER_VERTICAL|wx.TEXT_ALIGNMENT_RIGHT, indexAccel=-1)
        (comp, pronoun) = ('--', '--') if self.cur_competitor == -1 else self.competitors[self.cur_competitor]
        print(comp)
        competitor = comp + '\n (' + pronoun + ')'
        w, h = g.GetMultiLineTextExtent(competitor)
        cur_font = 44
        while w > 236 or h > 214:
            cur_font -= 1
            g.SetFont(wx.Font(cur_font, wx.DEFAULT, wx.NORMAL, wx.NORMAL, False, 'Narkisim'))
            w, h = g.GetMultiLineTextExtent(competitor)
        g.DrawLabel(competitor, empty_bmp, wx.Rect(1075, 50, 236, 214),
                    alignment=wx.ALIGN_TOP|wx.ALIGN_CENTER_HORIZONTAL, indexAccel=-1)
        for i in range(5):
            for j in range(3):
                cell = self.covered[5 * j + i]
                brush = wx.Brush(wx.Colour(lin_int(64, 249, cell), lin_int(64, 242, cell),
                                           lin_int(64, 255, cell), wx.ALPHA_OPAQUE))
                g.SetPen(self.frame_pen if self.framed[5 * j + i] else wx.BLACK_PEN)
                g.SetBrush(brush)
                hint, fandom = items[5 * j + i], fandoms[5 * j + i]
                g.DrawRoundedRectangle(50 + 300 * i, 264 + 200 * j, 250, 150, 15)

                newhint = adjust_font(g, hint, 200, 90, 5, 40)
                g.SetTextForeground('black')
                g.DrawLabel(newhint, empty_bmp, wx.Rect(50 + 300 * i, 264 + 200 * j, 250, 90),
                            alignment=wx.ALIGN_CENTER, indexAccel=-1)

                newfandom = adjust_font(g, fandom, 250, 60, 5, min(30, g.GetFont().GetPointSize()))
                g.SetTextForeground('grey')
                g.DrawLabel(newfandom, empty_bmp, wx.Rect(50 + 300 * i, 90 + 264 + 200 * j, 250, 60),
                            alignment=wx.ALIGN_CENTER, indexAccel=-1)

        # Draw 'keep'/'dump' buttons
        brush = wx.Brush(wx.Colour(249, 242, 255, wx.ALPHA_OPAQUE))
        g.SetBrush(brush)
        g.SetPen(wx.TRANSPARENT_PEN)
        keep_rect = wx.Rect(1536 - 50 - 150, 100, 150, 50)
        dump_rect = wx.Rect(1536 - 50 - 150, 164, 150, 50)
        reset_rect = wx.Rect(1536 - 50 - 150, 36, 150, 50)
        g.DrawRectangle(keep_rect)
        g.DrawRectangle(dump_rect)
        g.DrawRectangle(reset_rect)
        g.SetTextForeground('black')
        g.SetFont(wx.Font(30, wx.DEFAULT, wx.NORMAL, wx.FONTWEIGHT_SEMIBOLD, False, 'Narkisim'))
        g.DrawLabel('שמור', empty_bmp, keep_rect, alignment=wx.ALIGN_CENTER, indexAccel=-1)
        g.DrawLabel('שמוט', empty_bmp, dump_rect, alignment=wx.ALIGN_CENTER, indexAccel=-1)
        g.DrawLabel('איפוס', empty_bmp, reset_rect, alignment=wx.ALIGN_CENTER, indexAccel=-1)

    def key_handler(self, e):
        k = e.GetKeyCode()
        if k == wx.WXK_ESCAPE:
            sys.exit(0)
        if k == wx.WXK_RETURN:
            self.next_question()
            self.Refresh()

    def lclick_handler(self, e):
        mx, my = e.GetPosition()
        mx = self.GetSize().GetWidth() - mx
        if within_aabb(mx, my, 1536 - 50 - 150, 100, 150, 50):  # Keep
            ans = self.questions[self.curq]['answer' + str(self.innerq + 1)]
            self.framed = [0 for _ in range(15)]
            for i in range(15):
                if i not in ans:
                    if not self.covered[i]:
                        self.framed[i] = True
                    self.covered[i] = 1
            self.Refresh()
        if within_aabb(mx, my, 1536 - 50 - 150, 164, 150, 50):  # Dump
            ans = self.questions[self.curq]['answer' + str(self.innerq + 1)]
            self.framed = [0 for _ in range(15)]
            for i in range(15):
                if i in ans:
                    if not self.covered[i]:
                        self.framed[i] = True
                    self.covered[i] = 1
            self.Refresh()
        if within_aabb(mx, my, 1536 - 50 - 150, 36, 150, 50):  # Reset
            self.framed = [0 for _ in range(15)]
            self.covered = [0 for _ in range(15)]
            self.Refresh()
        if within_aabb(mx, my, 1075, 50, 236, 214):
            self.cur_competitor += 1
            if self.cur_competitor == len(self.competitors):
                self.cur_competitor = -1
            self.Refresh()

    def next_question(self):
        self.framed = [0 for _ in range(15)]
        if self.innerq:
            if self.curq < len(self.questions) - 1:
                self.innerq = 0
                self.curq += 1
        else:
            self.innerq = 1

    def read_questions(self):
        with open('questions.json', encoding='utf8') as f:
            q = json.load(f)['questions']
        first = q[0]
        q = q[1:]
        shuffle(q)
        self.questions = [first] + q

    def load_competitors(self):
        with open('Keep it or Dump it Registration.csv', encoding='utf8') as f:
            lines = f.read().split('\n')[1:]
        self.competitors = [(l.split(',')[1][1:-1], l.split(',')[2][1:-1]) for l in lines]
        shuffle(self.competitors)


if __name__ == '__main__':
    app = wx.App()
    frame = MyFrame()
    app.MainLoop()

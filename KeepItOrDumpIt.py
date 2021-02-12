import wx
import sys
from collections import namedtuple
from random import  shuffle


Question = namedtuple('Question', ['topic', 'items', 'q1', 'q2'])


def scale_bitmap(bitmap, width, height):
    image = bitmap.ConvertToImage()
    image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
    result = wx.Bitmap(image)
    return result


def within_aabb(x, y, xx, yy, w, h):
    return xx <= x < xx + w and yy <= y < yy + h


def remove_newlines(s):
    return ''.join(s.split('\n'))


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

        self.covered = [True for _ in range(15)]

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

        topic, items, q1, q2 = self.questions[self.curq]
        q = (q1, q2)
        g.SetTextForeground('white')
        g.SetFont(wx.Font(44, wx.DEFAULT, wx.NORMAL, wx.NORMAL, False, 'Narkisim'))
        empty_bmp = wx.Bitmap()
        title = 'נושא: ' + topic + '\nשאלה: ' + q[self.innerq]
        w, h = g.GetMultiLineTextExtent(title)
        cur_font = 44
        while w > 1000 and h > 214:
            cur_font -= 1
            g.SetFont(wx.Font(cur_font, wx.DEFAULT, wx.NORMAL, wx.NORMAL, False, 'Narkisim'))
            w, h = g.GetMultiLineTextExtent(title)
        g.DrawLabel(title, empty_bmp, wx.Rect(50, 50, 1000, 214),
                    alignment=wx.ALIGN_CENTER_VERTICAL|wx.TEXT_ALIGNMENT_RIGHT, indexAccel=-1)
        g.SetPen(wx.BLACK_PEN)
        for i in range(5):
            for j in range(3):
                if self.covered[5 * j + i]:
                    brush = wx.Brush(wx.Colour(249, 242, 225, wx.ALPHA_OPAQUE))
                    g.SetBrush(brush)
                else:
                    brush = wx.Brush(wx.Colour(64, 64, 64, wx.ALPHA_OPAQUE))
                    g.SetBrush(brush)
                hint, fandom = items[5 * j + i]
                g.DrawRoundedRectangle(50 + 300 * i, 264 + 200 * j, 250, 150, 15)

                newhint = adjust_font(g, hint, 200, 100, 5, 40)
                g.SetTextForeground('black')
                g.DrawLabel(newhint, empty_bmp, wx.Rect(50 + 300 * i, 264 + 200 * j, 250, 100),
                            alignment=wx.ALIGN_CENTER, indexAccel=-1)

                newfandom = adjust_font(g, fandom, 250, 50, 5, min(30, g.GetFont().GetPointSize()))
                g.SetTextForeground('grey')
                g.DrawLabel(newfandom, empty_bmp, wx.Rect(50 + 300 * i, 100 + 264 + 200 * j, 250, 50),
                            alignment=wx.ALIGN_CENTER, indexAccel=-1)

        # Draw 'keep'/'dump' buttons
        g.SetBrush(brush)
        g.SetPen(wx.TRANSPARENT_PEN)
        keep_rect = wx.Rect(1536 - 50 - 150, 100, 150, 50)
        dump_rect = wx.Rect(1536 - 50 - 150, 164, 150, 50)
        g.DrawRectangle(keep_rect)
        g.DrawRectangle(dump_rect)
        g.SetTextForeground('black')
        g.SetFont(wx.Font(30, wx.DEFAULT, wx.NORMAL, wx.FONTWEIGHT_SEMIBOLD, False, 'Narkisim'))
        g.DrawLabel('שמור', empty_bmp, keep_rect, alignment=wx.ALIGN_CENTER, indexAccel=-1)
        g.DrawLabel('שמוט', empty_bmp, dump_rect, alignment=wx.ALIGN_CENTER, indexAccel=-1)

    def key_handler(self, e):
        k = e.GetKeyCode()
        if k == wx.WXK_ESCAPE:
            sys.exit(0)

    def lclick_handler(self, e):
        mx, my = e.GetPosition()
        mx = self.GetSize().GetWidth() - mx
        if within_aabb(mx, my, 1536 - 50 - 150, 100, 150, 50):  # Keep
            self.next_question()
            self.Refresh()
        if within_aabb(mx, my, 1536 - 50 - 150, 164, 150, 50):  # Dump
            self.next_question()
            self.Refresh()

    def next_question(self):
        if self.innerq:
            if self.curq < len(self.questions) - 1:
                self.innerq = 0
                self.curq += 1
        else:
            self.innerq = 1

    def read_questions(self):
        lines = []

        with open('questions.txt', encoding='utf8') as f:
            lines = f.readlines()

        i = 0
        while i < len(lines):
            l = lines[i]
            if l[0] == '#':
                q = Question(remove_newlines(l[1:]),
                             [tuple([remove_newlines(s) for s in lines[i + j].split('|')]) for j in range(1, 16)],
                             remove_newlines(lines[i + 16]), remove_newlines(lines[i + 17]))
                i += 18
                self.questions.append(q)

        shuffle(self.questions)


if __name__ == '__main__':
    app = wx.App()
    frame = MyFrame()
    app.MainLoop()

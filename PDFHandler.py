# -*- coding: utf-8 -*-

import re
import pdfplumber
import numpy as np

import matplotlib.pyplot as plt

class VectorFigureExtraction:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path.split('/')[-1]
        self.pdf_handler = pdfplumber.open(pdf_path)
    
    def Run(self):
        self._LoadIndexFromPDF()
        for index in self.pages:
            self._LoadNoteFromPage(index)
            if(self.note_begs == []):
                continue
            self._LoadAxisFromPage(index)
            self._LoadCurveFromPage(index)
            self._LoadTransformation(index)
            txt_path = 'result/{}_{}_text.txt'.format(self.pdf_path, index)
            self.Print(txt_path)
            fig_paths = ['result/{}_{}_{}_figure.png'.format(self.pdf_path, index, i) for i in range(len(self.mine_transformed_dot_values))]
            self.Draw(fig_paths)
        self.pdf_handler.close()
        
    def Print(self, txt_path):
        text = ""
        for (k, key) in enumerate(self.mine_transformed_dot_values):
            text += "The {}-th figure\n".format(k)
            for (i, dots) in enumerate(self.mine_transformed_dot_values[key]):
                text += "\t The {}-th dots\n".format(i)
                for dot in dots:
                    text += "\t\t ({},{})\n".format(dot[0], dot[1])
        with open(txt_path, 'w+', encoding = 'utf-8') as f:
            f.write(text.strip())
    
    def Draw(self, fig_paths):
        for (k, key) in enumerate(self.mine_transformed_dot_values):
            fig=plt.figure(figsize=(6,6))
            ax=fig.add_subplot(111)
            for (i, dots) in enumerate(self.mine_transformed_dot_values[key]):
                xvalue = list()
                yvalue = list()
                for dot in dots:
                    xvalue.append(dot[0])
                    yvalue.append(dot[1])
                ax.plot(xvalue, yvalue, linewidth = 4)
            ax.tick_params(axis='both',which='both',direction='out',width=1,length=10, labelsize=35)
        
            bwith=4
            ax.spines['bottom'].set_linewidth(bwith)
            ax.spines['left'].set_linewidth(bwith)
            ax.spines['right'].set_visible(False)
            ax.spines['top'].set_visible(False)
            plt.xlabel('$x$',fontsize=45)
            plt.ylabel('$y$',fontsize=45)
            plt.xticks(fontsize=30)
            plt.yticks(fontsize=30)
            plt.tight_layout()
            plt.savefig(fig_paths[k], dpi = 300)
            plt.show()
    
    def _LoadIndexFromPDF(self):
        print('Start to load index from pdf.')
        pages = list()
        for (i, page) in enumerate(self.pdf_handler.pages):
            if(len(page.annots) == 0):
                continue
            else:
                pages.append(i)
        self.pages = pages
        
    def _LoadNoteFromPage(self, index):
        print('Start to load note data from page {} of pdf.'.format(index))
        page = self.pdf_handler.pages[index]
        begs = list()
        ends = list()
        for (i, annot) in enumerate(page.annots):
            content = annot.get('contents')
            if(content == None):
                continue
            x0 = annot.get('x0')
            x1 = annot.get('x1')
            y0 = annot.get('y0')
            y1 = annot.get('y1')
            if(int(content) % 2 == 1):
                begs.append((min(x0, x1), min(y0, y1)))
            else:
                ends.append((max(x0, x1), max(y0, y1)))
        self.note_begs = begs
        self.note_ends = ends
    
    def __axis_add(self, dic, key, value):
        if(key in dic):
            dic[key].append(value)
            return;
        for similar_key in dic:
            if(np.abs(similar_key - key) < 0.005):
                dic[similar_key].append(value)
                return;
        if(key not in dic):
            dic[key] = list()
            dic[key].append(value)
    
    def __axis_sort(self, dic):
        for key in dic:
            dic[key] = sorted(dic[key], key = lambda x: x['xy'])
    
    def __axis_in(self, beg, end, x, y):
        if(x > beg[0] and x < end[0] and y < beg[1] and y > end[1]):
            return True
        else:
            return False
        
    def __axis_combine_number(self, old_list):
        item_former = None
        new_list = list()
        for item in old_list:
            if(item_former == None):
                item_former = item
                continue
            x0_former = item_former['x0']
            y0_former = item_former['y0']
            x1_former = item_former['x1']
            y1_former = item_former['y1']
            x0 = item['x0']
            y0 = item['y0']
            x1 = item['x1']
            y1 = item['y1']
            flag = 0
            if(np.abs(x1_former - x0) < 1e-8):
                item_former['text'] = item_former['text'] + item['text']
                item_former['x1'] = item['x1']
                flag = 1
            if(np.abs(y1_former - y0) < 1e-8):
                item_former['text'] = item_former['text'] + item['text']
                item_former['y1'] = item['y1']
                flag = 1
            if(np.abs(x1 - x0_former) < 1e-8):
                item_former['text'] =  item['text'] + item_former['text']
                item_former['x0'] = item['x0']
                flag = 1
            if(np.abs(y1 - y0_former) < 1e-8):
                item_former['text'] = item['text'] + item_former['text']
                item_former['y0'] = item['y0']
                flag = 1
            if(flag == 0):
                new_list.append(item_former)
                item_former = item
        return new_list
    
    def __axis_search_axis(self, dic):
        axises = None
        for key in dic:
            item = dic[key]
            unchecked_list = [t['text'] for t in item]
            # print(unchecked_list)
            count = 0
            max_count = len(unchecked_list) - 2
            if(max_count <= 0):
                continue
            for i in range(1, len(unchecked_list) - 1):
                if(2 * unchecked_list[i] == unchecked_list[i-1] + unchecked_list[i+1]):
                    count += 1
            if(count / max_count > 0.75):
                axises = item
                break
        return axises
    
    def _LoadAxisFromPage(self, index):
        print('Start to load axis data from page {} of pdf.'.format(index))
        mine_xvalues = dict()
        mine_yvalues = dict()
        page = self.pdf_handler.pages[index]
        chars = page.objects.get('char')
        old_mine_dict = dict()
        new_mine_dict = dict()
        for (i, j) in zip(self.note_begs, self.note_ends):
            old_mine_dict[(i, j)] = list()
            new_mine_dict[(i, j)] = list()
        for char in chars:
            if(('text' not in char) or ('x0' not in char) or ('y0' not in char)):
                continue
            if(re.match(r'(^[-+]?([1-9][0-9]*|0)(\.[0-9]+)?$)', char['text']) or char['text'] == '.'):
                for key in old_mine_dict:
                    if(self.__axis_in(key[0], key[1], char['x0'], char['y0'])):
                        old_mine_dict[key].append(char)
        
        for key in old_mine_dict:
            new_mine_dict[key] = self.__axis_combine_number(old_mine_dict[key])
            
        for key in new_mine_dict:
            xvalues = dict()
            yvalues = dict()
            for char in new_mine_dict[key]:
                xaxis = char['x1']
                xaxis = round(xaxis, 4)
                yaxis = char['y0']
                yaxis = round(yaxis, 4)
                text = char['text']
                self.__axis_add(xvalues, xaxis, {'text' : float(text), 'xy' : (char['y0'] + char['y1']) / 2})
                self.__axis_add(yvalues, yaxis, {'text' : float(text), 'xy' : (char['x0'] + char['x1']) / 2})
            self.__axis_sort(xvalues)
            self.__axis_sort(yvalues)
            mine_xvalues[key] = xvalues
            mine_yvalues[key] = yvalues
        
        xvols = dict()
        yvols = dict()
        for key in new_mine_dict:
            xvalues = mine_xvalues[key]
            yvalues = mine_yvalues[key]
            xvol = self.__axis_search_axis(xvalues)
            yvol = self.__axis_search_axis(yvalues)
            xvols[key] = xvol
            yvols[key] = yvol
            if(xvol == None or yvol == None):
                print("")
        self.xvols = xvols
        self.yvols = yvols
        
    def _LoadTransformation(self, index):
        mine_transformed_dot_values = dict()
        for key in self.xvols:
            mine_transformed_dot_values[key] = list()
        for key in self.xvols:
            x_dots1 = (self.xvols[key][0]['text'], self.xvols[key][0]['xy'])
            x_dots2 = (self.xvols[key][1]['text'], self.xvols[key][1]['xy'])
            y_dots1 = (self.yvols[key][0]['text'], self.yvols[key][0]['xy'])
            y_dots2 = (self.yvols[key][1]['text'], self.yvols[key][1]['xy'])
            fun_y = lambda y : x_dots1[0] + (x_dots1[0] - x_dots2[0]) * (y - x_dots1[1]) / (x_dots1[1] - x_dots2[1])
            fun_x = lambda y : y_dots1[0] + (y_dots1[0] - y_dots2[0]) * (y - y_dots1[1]) / (y_dots1[1] - y_dots2[1])
            for dots in self.mine_dot_values[key]:
                transformed_dots = list()
                for dot in dots:
                    transformed_dots.append((fun_x(dot[0]), fun_y(dot[1])))
                mine_transformed_dot_values[key].append(transformed_dots)
            
        self.mine_transformed_dot_values = mine_transformed_dot_values
    
    def _LoadLineFromPage(self, index):
        fig=plt.figure(figsize=(6,6))
        ax=fig.add_subplot(111)
        print('Start to load line data from pdf.')
        text = ""
        page = self.pdf_handler.pages[index]
        lines = page.objects.get('line')
        for line in lines:
            if('pts' in line):
                dots = line['pts']
                for dot in dots:
                    ax.scatter(dot[0], dot[1])
        return text
    
    def _LoadCurveFromPage(self, index):
        print('Start to load curve data from pdf.')
        page = self.pdf_handler.pages[index]
        mine_dot_values = dict()
        for (i, j) in zip(self.note_begs, self.note_ends):
            mine_dot_values[(i, j)] = list()
        
        curves = page.objects.get('curve')
        for curve in curves:
            if('pts' in curve):
                dots = curve['pts']
            for key in mine_dot_values:
                if(self.__axis_in(key[0], key[1], dots[0][0], dots[0][1]) and len(dots) > 20):
                    mine_dot_values[key].append(dots)
        self.mine_dot_values = mine_dot_values
        
if __name__ == "__main__":
    pdf_path = "pdfs/nejmoa2114663.pdf"
    pdf = VectorFigureExtraction(pdf_path)
    pdf.Run()
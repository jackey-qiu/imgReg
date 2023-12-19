# step by step configuration

0. assume you have conda installed in the sys, if not, do it.
1. run this command to create a new conda env named img `conda create --name img python==3.10.0 --no-default-packages`
2. cd to the root folder of imgReg, where you should see a requirements.txt file
3. run this command to install all dependend packages `pip install -r requirements.txt`
4. There is some issue with the console module in pyqtgraph. You should locate this file 'site-packages\pyqtgraph\console\Console.py' in the current conda env (i.e. img).Change the following three lines
- line 120 `self.write("<br><b>%s</b>\n"%encCmd, html=True, scrollToBottom=True)` changed to `self.write("<br><b>%s</b>\n"%encCmd, html=True)`
- line 123 `self.write("<br><div style='background-color: #CCF; color: black'><b>%s</b>\n"%encCmd, html=True, scrollToBottom=True)` changed to `self.write("<br><div style='background-color: #CCF; color: black'><b>%s</b>\n"%encCmd, html=True)`
- line 128 `self.write("</div>\n", html=True, scrollToBottom=True) changed to self.write("</div>\n", html=True)`
5. now you are all set.
6. cd to the folder where entry script is located: `cd imgReg\imgReg\core\src`
7. Before firing up the main program, you should edit the config file accordingly, imgReg\imgReg\config\appsettings.ini, change the values for **restoreimagedb** and **currentimagedbDir** accordingly.
8. run the cmd: `python workspace.py`

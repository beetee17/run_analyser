import gpxpy ## For parsing .gpx files
from geopy import distance ## For calculating spherical distances btw coordinates
import matplotlib.pyplot as plt
from datetime import datetime
from math import sqrt, floor
import numpy as np
import pandas as pd
import os

## Tutorial: https://towardsdatascience.com/how-tracking-apps-analyse-your-gps-data-a-hands-on-tutorial-in-python-756d4db6715d

def view_df(df):
    """Prints entire dataframe for debugging purposes"""
    with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
        print(df)
        
def gpx_to_df(filename):
    
    with open(filename, 'r') as gpx_file:
        
        gpx = gpxpy.parse(gpx_file)
        
##        print(len(gpx.tracks),
##              len(gpx.tracks[0].segments),
##              len(gpx.tracks[0].segments[0].points))
    ##    Check that data points are stored in a single gpx track & segment

        data = gpx.tracks[0].segments[0].points
        try:
            data += gpx.tracks[0].segments[1].points
        except IndexError:
            pass
        
        df = pd.DataFrame(columns=['lon', 'lat', 'alt', 'time'])
        
        start_time = data[0].time
        
        for point in data:

            delta_time = point.time - start_time
                    
            df = df.append({'lon': point.longitude,
                            'lat' : point.latitude,
                            'alt' : point.elevation,
                            'time' : delta_time.total_seconds()}, ignore_index=True)

    return df

def get_activity_map(df, filename, save = False):
    plt.plot(df['lon'], df['lat'])
    fname = filename.replace(".gpx", "")
    plt.title(fname.replace("_", " "))
    if save:
        try:
            os.mkdir("{}".format(fname))
        except Exception as e:
            print(e)
            pass
        plt.savefig("{}/{}_ACTIVITY_MAP".format(fname, fname))
    plt.show()
    
def get_altitude_graph(df, filename, save = False):
    plt.plot(df['time'], df['alt'])
    fname = filename.replace(".gpx", "")
    plt.title(fname.replace("_", " "))
    if save:
        try:
            os.mkdir("{}".format(fname))
        except Exception as e:
            print(e)
            pass
        plt.savefig("{}/{}_ALTITUDE".format(fname, fname))
    plt.show()
    
def get_pace_graph(df, filename, save = False):
    y_low = 2
    y_upp = 5.6
    fig, ax = plt.subplots()
    fname = filename.replace(".gpx", "")
    plt.title(fname.replace("_", " "))
    plt.xlabel('Time (s)')
    plt.ylabel('Pace (min/km)')
    ax.plot(df['time'], df['pace (min/km)'])
    ax.set_ylim(y_upp, y_low)
    plt.yticks(np.arange(y_low, y_upp, 0.2))
    plt.fill_between(df['time'], y_upp, df['pace (min/km)'])
    if save:
        try:
            os.mkdir("{}".format(fname))
        except Exception as e:
            print(e)
            pass
        plt.savefig("{}/{}_PACE".format(fname, fname))
    plt.show()

def get_dist_time_graph(df, filename, save = False):
    fname = filename.replace(".gpx", "")
    plt.plot(df['time'], df['distance'])
    plt.title(fname.replace("_", " "))
    plt.xlabel('Time (s)')
    plt.ylabel('Distance (m)')
    if save:
        try:
            os.mkdir("{}".format(fname))
        except Exception as e:
            print(e)
            pass
        plt.savefig("{}/{}_DISTANCE".format(fname, fname))
    plt.show()
    
def get_cumulative_dist(df):
    distances = [0]
    for index in range(1,len(df)):
        prev = index - 1
        step = distance.vincenty((df.loc[prev, 'lat'], df.loc[prev, 'lon']),
                                 (df.loc[index, 'lat'], df.loc[index, 'lon'])).m
        distances.append(step + distances[-1])
        
    df['distance'] = distances
    
    return df

def get_pace_df(df, step):
    """Calculates average pace between a specified time step
        Time steps may not correspond to seconds elapsed! (Data
        may not have recorded at every second during activity)

        Requires df to include columns for cumulative distance and time"""
    
    paces = []
    
    for count in range(step):
            paces.append(np.NaN)
            
    for index in range(step, len(df), step):
        
        if index < len(df) - 1:
            if index != step:
                for count in range(step - 1):
                    paces.append(np.NaN)
                    
        prev = index - step
        dist = df.loc[index, 'distance'] - df.loc[prev, 'distance']
        time = df.loc[index, 'time'] - df.loc[prev, 'time']
        pace =  1 / (dist/time *0.06)
        paces.append(pace)
        
    while len(paces) < len(df):
        paces.append(np.NaN)
        
    df['pace (min/km)'] = paces
    df.replace(0, np.NaN, inplace = True)
    df = df.dropna()
    
    return df.reset_index(drop = True)
def get_laps(pace_df, filename, lap_dist, save = False):

    fname = filename.replace(".gpx", "")
    laps = [pace_df.loc[0, :]]
    
    if save:
        try:
            os.mkdir("{}".format(fname))
        except Exception as e:
            print(e)
            pass
        save_file = open("{}/{}_ANALYSIS.txt".format(fname, fname), 'a+') 
        save_file.write("\nANALYSIS OF {}\n\n".format(fname.replace("_", " ")))
        
    for dist in range(lap_dist, 20000, lap_dist):
        for i in range(1, len(pace_df)):
            if pace_df.loc[i, 'distance'] > dist:
                laps.append(pace_df.loc[i, :])
                break
            
    laps.append(pace_df.loc[len(pace_df) - 1, :])
   
    for i in range(len(laps) - 1):
        if i == 0:
            split_time = laps[i+1].time 
            dist = laps[i+1].distance 
            avg_pace = 1 / (dist/split_time *0.06)
            avg_pace_seconds = round(avg_pace * 60 % 60, 1)
            per_hundred_pace = round(split_time/(dist/100), 2)
            
        else:
            split_time = laps[i+1].time - laps[i].time
            dist = laps[i+1].distance - laps[i].distance
            avg_pace = 1 / (dist/split_time *0.06)
            avg_pace_seconds = round(avg_pace * 60 % 60, 1)
            per_hundred_pace = round(split_time/(dist/100), 2)

        if save:
            save_file.write("LAP {} \nTIME: {}s \nDISTANCE: {}m \nAVERAGE PACE: {}:{:04.1f} min/km OR {} s/100m\n\n".format(i + 1, split_time, round(dist, 2), int(avg_pace), avg_pace_seconds, per_hundred_pace))

        print("LAP {} \nTIME: {}s \nDISTANCE: {}m \nAVERAGE PACE: {}:{:04.1f} min/km OR {} s/100m\n".format(i + 1, split_time, round(dist, 2), int(avg_pace), avg_pace_seconds, per_hundred_pace))

    
        

def view_splits(pace_df, filename, debug = False, save = False):
    """Intelligently deduces the start and end of each split/rest cycle and
    prints out timings, distance covered and average pace"""
    
    RUN_THRESHOLD = 5 ## Pace threshold whereby resting is defined as above it, and running as below it
    REST_THRESHOLD = 6
    RUN_THRESHOLD_COUNT = 6 ## Additional threshold to filter out noise in data that causes large but momentary fluctuations in pace values  
    REST_THRESHOLD_COUNT = 2
    resting = None
    running = None
    
    start_run = []
    start_rest = []
    fname = filename.replace(".gpx", "")
    
    if save:
        try:
            os.mkdir("{}".format(fname))
        except Exception as e:
            print(e)
            pass
        save_file = open("{}/{}_ANALYSIS.txt".format(fname, fname), 'a+') 
        save_file.write("\nANALYSIS OF {}\n\n".format(fname.replace("_", " ")))

    print("\nANALYSIS OF {}\n".format(fname.replace("_", " ")))
    for time_step in range(len(pace_df)):
        if pace_df.loc[time_step, 'pace (min/km)'] > REST_THRESHOLD:
            count = 0
            ## Runner may have started to rest
            for i in range(1, REST_THRESHOLD_COUNT + 1):
                if pace_df.loc[min(time_step + i, len(pace_df) - 1), 'pace (min/km)'] > REST_THRESHOLD:
                    ## Check that future running pace values all corroborate resting 'hypothesis'
                    count += 1
        
            if count >= REST_THRESHOLD_COUNT:
                ## Runner most likely just started resting
                if not resting:
                    running = False
                    resting = True
                    start_rest.append(pace_df.loc[max(time_step-1, 0), :])
    
        elif pace_df.loc[time_step, 'pace (min/km)'] < RUN_THRESHOLD:
            count = 0
            ## Runner may have started to run
            for i in range(1, RUN_THRESHOLD_COUNT + 1):
                if pace_df.loc[min(time_step + i, len(pace_df) - 1), 'pace (min/km)'] < RUN_THRESHOLD:
                    ## same logic as above
                    count += 1
                
            if count >= RUN_THRESHOLD_COUNT - 1:
                if not running:
                    running = True
                    resting = False
                    start_run.append(pace_df.loc[time_step, :])

    if len(start_rest) > len(start_run):
        start_rest = start_rest[1:]
    elif len(start_rest) < len(start_run):
        start_rest.append(pace_df.iloc[-1])
    for i in range(len(start_run)):
        split_time = start_rest[i].time - start_run[i].time
        dist = start_rest[i].distance - start_run[i].distance
        avg_pace = 1 / (dist/split_time *0.06)
        avg_pace_seconds = round(avg_pace * 60 % 60, 1)
        per_hundred_pace = round(split_time/(dist/100), 2)
        
        if i < len(start_run) - 1:
            rest_time = start_run[i + 1].time - start_rest[i].time
            
            if save:
                save_file.write("LAP {} \nTIME: {}s \nDISTANCE: {}m \nAVERAGE PACE: {}:{:04.1f} min/km OR {} s/100m\nREST: {}s\n\n".format(i + 1, split_time, round(dist, 2), int(avg_pace), avg_pace_seconds, per_hundred_pace, rest_time))

            print("LAP {} \nTIME: {}s \nDISTANCE: {}m \nAVERAGE PACE: {}:{:04.1f} min/km OR {} s/100m\nREST: {}s\n".format(i + 1, split_time, round(dist, 2), int(avg_pace), avg_pace_seconds, per_hundred_pace, rest_time))
        else:
            
            if save:
                save_file.write("LAP {} \nTIME: {}s \nDISTANCE: {}m \nAVERAGE PACE: {}:{:04.1f} min/km OR {} s/100m\n\n".format(i + 1, split_time, round(dist, 2), int(avg_pace), avg_pace_seconds, per_hundred_pace))

            print("LAP {} \nTIME: {}s \nDISTANCE: {}m \nAVERAGE PACE: {}:{:04.1f} min/km OR {} s/100m\n".format(i + 1, split_time, round(dist, 2), int(avg_pace), avg_pace_seconds, per_hundred_pace))

    if debug:
        for i in range(len(start_run)):
            print("RUN {}\n{}".format(i+1, start_run[i]))
            print("REST {}\n{}".format(i+1, start_rest[i]))
            
    if save:
        save_file.close()
    
    return start_run, start_rest

from matplotlib.animation import FuncAnimation
import mpl_toolkits.axes_grid1
import matplotlib.widgets

class Player(FuncAnimation):
    def __init__(self, fig, func, frames=None, init_func=None, fargs=None,
                 save_count=None, mini=0, maxi=100, pos=(0.125, 0.92), **kwargs):
        self.i = 0
        self.min=mini
        self.max=maxi
        self.runs = True
        self.forwards = True
        self.fig = fig
        self.func = func
        self.setup(pos)
        FuncAnimation.__init__(self,self.fig, self.func, frames=self.play(), 
                                           init_func=init_func, fargs=fargs,
                                           save_count=save_count, **kwargs )    

    def play(self):
        while self.runs:
            self.i = self.i+self.forwards-(not self.forwards)
            if self.i > self.min and self.i < self.max:
                yield self.i
            else:
                self.stop()
                yield self.i

    def start(self):
        self.runs=True
        self.event_source.start()

    def stop(self, event=None):
        self.runs = False
        self.event_source.stop()

    def forward(self, event=None):
        self.forwards = True
        self.start()
    def backward(self, event=None):
        self.forwards = False
        self.start()
    def oneforward(self, event=None):
        self.forwards = True
        self.onestep()
    def onebackward(self, event=None):
        self.forwards = False
        self.onestep()

    def onestep(self):
        if self.i > self.min and self.i < self.max:
            self.i = self.i+self.forwards-(not self.forwards)
        elif self.i == self.min and self.forwards:
            self.i+=1
        elif self.i == self.max and not self.forwards:
            self.i-=1
        self.func(self.i)
        self.fig.canvas.draw_idle()

    def setup(self, pos):
        playerax = self.fig.add_axes([pos[0],pos[1], 0.22, 0.04])
        divider = mpl_toolkits.axes_grid1.make_axes_locatable(playerax)
        bax = divider.append_axes("right", size="80%", pad=0.05)
        sax = divider.append_axes("right", size="80%", pad=0.05)
        fax = divider.append_axes("right", size="80%", pad=0.05)
        ofax = divider.append_axes("right", size="100%", pad=0.05)
        self.button_oneback = matplotlib.widgets.Button(playerax, label=u'$\u29CF$')
        self.button_back = matplotlib.widgets.Button(bax, label=u'$\u25C0$')
        self.button_stop = matplotlib.widgets.Button(sax, label=u'$\u25A0$')
        self.button_forward = matplotlib.widgets.Button(fax, label=u'$\u25B6$')
        self.button_oneforward = matplotlib.widgets.Button(ofax, label=u'$\u29D0$')
        self.button_oneback.on_clicked(self.onebackward)
        self.button_back.on_clicked(self.backward)
        self.button_stop.on_clicked(self.stop)
        self.button_forward.on_clicked(self.forward)
        self.button_oneforward.on_clicked(self.oneforward)




    
def get_laps_df(pace_df, start_run, start_rest):
    laps = []

    for x in range(len(start_run)):
##        lap = pace_df.iloc[start_run[x].name : start_rest[x].name, :].reset_index()
        if x == len(start_run) - 1:
             lap = pace_df.iloc[start_run[x].name: , :].reset_index()
        else:
            lap = pace_df.iloc[start_run[x].name : start_run[x+1].name, :].reset_index()
        laps.append(lap)
    
    return laps

def view_map(pace_df, start_run, start_rest):
    
    def update(i):

        ## iteratively plot data      
        xdata.append(lon[i])
        ydata.append(lat[i])
        ln.set_data(xdata, ydata)


        ## update current pace, time and activity on graph
        pace_text = '{} min/km'.format(pace_df.loc[i, 'pace (min/km)'].round(2))
        live_pace.set_text(pace_text)
        time_text.set_text('{} s'.format(int(pace_df.loc[i, 'time'])))
    
        
        for x in range(len(start_run)):
                
            if i >= start_run[x].name and i < start_rest[x].name:
                ## running
                activity_text.set_text('RUNNING')
                ax.set_title('LAP {}'.format(x+1))
                
            elif i >= start_rest[x].name:
                
                ## resting
                if x < len(start_run) - 1:
                    if i < start_run[x+1].name:
                        activity_text.set_text('RESTING')
                else:
                    activity_text.set_text('RESTING')
                        
        

        return ln,
    
    fig, ax = plt.subplots()
    
    live_pace = ax.text(0.05, 0.95, 'NIL',
                        fontsize=14,
                        horizontalalignment='left',
                        transform=ax.transAxes)
    
    time_text = ax.text(0.5, 0.95, 'NIL',
                        fontsize=14,
                        horizontalalignment='center',
                        transform=ax.transAxes)
    
    activity_text = ax.text(0.95, 0.95, 'NIL',
                            fontsize=14,
                            horizontalalignment='right',
                            transform=ax.transAxes)
    
    xdata = []
    ydata = []
    
    lon = pace_df['lon']
    lat = pace_df['lat']
    scale = 0.0001
    
    ax.set_xlim(min(lon)*(1-scale), max(lon)*(1+scale))
    ax.set_ylim(min(lat)*(1-scale), max(lat)*(1+scale))
    
    ln, = plt.plot([], [], marker="None", color="b", ls = '-', lw = 2)
    ln.set_solid_capstyle('round')
    
    ani = Player(fig, update, mini = 0, maxi = len(pace_df)-1)

    plt.show()

    
if __name__ == "__main__":
    
    ## Finds any and all gpx files in placed directory and performs analysis on them
    file_count = 0
    gpx_files = []

    for filename in os.listdir():
        if ".gpx" in filename:
            file_count += 1
            gpx_files.append(filename)
            
    print("FOUND {} gpx file(s)".format(file_count))




    for i in range(file_count):
        filename = gpx_files[i]
        print("FILE {} of {}: {}".format(i+1, file_count, filename))
        df = gpx_to_df(filename)
        df = get_cumulative_dist(df)
        pace_df = get_pace_df(df, 1)

        view_df(pace_df)
        #get_pace_graph(get_pace_df(df, 3), filename, save = True)
        #get_dist_time_graph(df, filename, save = True)
        start_run, start_rest = view_splits(pace_df,
                                            filename,
                                            debug = True,
                                            save = True)
##        view_map(pace_df, start_run, start_rest)

##        get_laps(pace_df, filename, 400, save = True)

    

    

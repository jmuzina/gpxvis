
####generateVis
####code sources: https://github.com/pavel-perina/gpx_to_png

import base64
import glob
import io
import logging
import math
import os
import shutil
import sys
import urllib
from ast import Str

import gpxpy
from PIL import GifImagePlugin as pil_gif
from PIL import Image as pil_image
from PIL import ImageDraw as pil_draw
from PIL import ImageFilter as pil_filter
from PIL import ImageFont as pil_font
from PIL.ImageFilter import (BLUR, CONTOUR, DETAIL, EDGE_ENHANCE,
                             EDGE_ENHANCE_MORE, EMBOSS, FIND_EDGES, SHARPEN,
                             SMOOTH, SMOOTH_MORE)


def get_black_pixels(im, isGifFrame = False):
    """ get list of every black pixel in an image and their coordinate """
    width, height = im.size
    blackPixels = []

    #gifs store color slightly differently.
    if isGifFrame:
        for x in range(width):
            for y in range(height):
                color = im.getpixel((x,y))
                if color < 140: #check for pixels that are not white. 175 is rough estimate and can be changed in future to something more elaborate
                    blackPixels.append({"x":x,"y":y})
    else:
        for x in range(width):
            for y in range(height):
                color = im.getpixel((x,y))            
                if color > 0: #check for pixels that are not white, formerly < 200 for gif
                    blackPixels.append({"x":x,"y":y})
    return blackPixels
 

## osm functions taken from https://github.com/pavel-perina/gpx_to_png
def osm_lat_lon_to_x_y_tile (lat_deg, lon_deg, zoom):
    """ Gets tile containing given coordinate at given zoom level """
    ## taken from http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames, works for OSM maps and mapy.cz
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return (xtile, ytile)


def osm_get_auto_zoom_level ( min_lat, max_lat, min_lon, max_lon, max_n_tiles):
    """ Gets zoom level which contains at maximum `max_n_tiles` """
    for z in range (0,17):
        x1, y1 = osm_lat_lon_to_x_y_tile (min_lat, min_lon, z)
        x2, y2 = osm_lat_lon_to_x_y_tile (max_lat, max_lon, z)
        max_tiles = max (abs(x2 - x1), abs(y2 - y1))
        if (max_tiles > max_n_tiles):
            #print ("Max tiles: %d" % max_tiles)
            return z 
    return 17

#given number of activities, return optimal grid dimensions for facets
def get_dimensions(n):
    for x in range(0,100): #100 is maximum amount of rows and columns allowed
        if(n <= (x+1)**2):
            #print("x: " + str(x))
            #print("maxRows: " + str((x+1)**2))
            return(x+1)
    print("failed to get dimensions")
    return(0)

def save_image(image, filename = ""):
    if filename != "":
            image.save (filename)
            #image.show()
        # no file name provided, return image as base64-encoded string for displaying without saving on server
    else:
        imgArray = io.BytesIO()
        image.save(imgArray, format="PNG")
        return str(base64.b64encode(imgArray.getvalue()), 'utf-8')
    #print("Saving " + filename) 
    image.save(filename)
    #image.show()
            
##this class is the canvas that the activities(tracks) will be drawn on.
class ImageCreator:
    def __init__(self, tracks, lineThickness = 5, backgroundColor = (255,255,255), backgroundImage = "", backgroundBlur = 5, foregroundColor = (0,0,0), gridOn = False, gridColor = (255,255,255), gridThickness = 1,  title = "", silhouetteImage = None, duplicateActivities = False, textBackgroundFade = False, infoText = False, totalTime = "", totalDistance = ""):
        
        self.tracks = tracks
        
        ##sizing##
        self.resolution = 4000
        self.maxTileWidth = self.resolution/(self.get_max_track_width())
        if silhouetteImage==None: 
            self.maxRows = get_dimensions(len(tracks))
        else:
            print(silhouetteImage)
            self.maxRows = silhouetteImage.height
        self.width = self.resolution #500 * self.maxRows
        self.height = self.width
        self.tile_res = self.maxTileWidth/self.maxRows
        self.gridElementSize = self.width / self.maxRows
        #print("Max track width: " + str(self.get_max_track_width()))
        #print("Max tile width: " + str(self.maxTileWidth))
        
        ##user parameters##
        self.lineThickness = lineThickness 
        self.gridColor = gridColor
        self.foregroundColor = foregroundColor
        self.gridOn = gridOn
        self.gridThickness = gridThickness
        self.textBackgroundFade = textBackgroundFade
        self.infoText = infoText
        self.duplicateActivities = duplicateActivities

        ##statistics##
        self.totalTime = totalTime
        self.totalDistance = totalDistance
        
        ####background image####
        
        if backgroundImage!="":
            self.backgroundImageFilePath = "uploads/" + backgroundImage
            backgroundImage = pil_image.open(self.backgroundImageFilePath)

            ##resize and crop image to fit##
            if(backgroundImage.width < self.resolution or backgroundImage.height < self.resolution):
                if(backgroundImage.width>backgroundImage.height):
                    backgroundImage = backgroundImage.resize((backgroundImage.width*(math.ceil(self.resolution/backgroundImage.height)),self.resolution))
                else:
                    backgroundImage = backgroundImage.resize((self.resolution,backgroundImage.height*(math.ceil(self.resolution/backgroundImage.width))))
            backgroundImage = backgroundImage.crop(((backgroundImage.width-self.resolution)/2,(backgroundImage.height-self.resolution)/2, (backgroundImage.width+self.resolution)/2,(backgroundImage.height+self.resolution)/2))
            backgroundImage = backgroundImage.filter(pil_filter.GaussianBlur(int(backgroundBlur)))
            backgroundImage = backgroundImage.convert("RGBA")
            self.image = backgroundImage
        else:
            self.image = pil_image.new ("RGBA", (self.width, self.height), backgroundColor)

           
    def draw_overlay(self):
        ## draw things that overlay image, such as text, text backgroudn fade, and grid

        if(self.textBackgroundFade == True):
            fade = pil_image.open("static/fade.png").resize((self.resolution,self.resolution))
            self.image = pil_image.alpha_composite(self.image, fade)

        if (self.gridOn==True): 
            self.draw_grid()

        if (self.infoText==True):
            if self.totalDistance != "":
                self.draw_statistic("distance",self.totalDistance, "left")
            if self.totalTime != "":
                self.draw_statistic("time", self.totalTime,"center")
                
            self.draw_statistic("activities",str(self.get_tracks_length()),"right") #str(self.get_tracks_length())
     
    def draw_statistic(self,label="",text="", position="center"):
        ## draw statistic in either left, right, or middle of image ##
        draw = pil_draw.Draw(self.image)
        textFont = pil_font.truetype('static/aileron/Aileron-Regular.otf', int(self.width/13)) #300
        labelFont = pil_font.truetype('static/aileron/Aileron-Regular.otf', int(self.width/30)) #130
        
        # calculate the x,y coordinates of the text
        textwidth, textheight = draw.textsize(text, textFont)
        labelwidth, labelheight = draw.textsize(label, labelFont)
        margin = self.width/40 #self.width is resolution
        textx = 0
        texty = 0
    
        if position=="right":
            textx = self.image.width - labelwidth - margin
            texty = self.image.height - textheight - margin
        elif position=="left":
            textx = 0
            texty = self.image.height - textheight - margin
        elif position=="center":
            textx = self.image.width/2 - (textwidth/2)
            texty = self.image.height - textheight - margin
                    

        labelx = (textx + textwidth/2)-(labelwidth/2) #+ math.ceil(textwidth*.05)
        labely = texty-(textheight/2)
        
        draw.text((textx, texty), text, font=textFont, align='center') #align='center'
        draw.text((labelx, labely), label, font=labelFont)
        
        del draw
    def draw_grid(self):
        ## draw grid lines ##
        step_count = self.maxRows
        
        draw = pil_draw.Draw (self.image)
        y_start = 0
        y_end = self.image.height
        step_size = int(self.image.width / step_count)
        for x in range(0, self.image.width, step_size):
            line = ((x, y_start), (x, y_end))
            draw.line(line, fill=self.gridColor, width=self.gridThickness)
        x_start = 0
        x_end = self.image.width
        for y in range(0, self.image.height, step_size):
            line = ((x_start, y), (x_end, y))
            draw.line(line, fill=self.gridColor, width=self.gridThickness)
        del draw
    def draw_facets(self):
        row = 0
        column = 0
        gridElementSize = self.width / self.maxRows
        for track in self.tracks:
            if column == self.maxRows:
                row+=1
                column = 0

            #center tracks. set to zero to uncenter
            centerxOffset = (self.gridElementSize/2) - (track.get_width()*self.tile_res)/2
            centeryOffset = (self.gridElementSize/2) -(track.get_height()*self.tile_res)/2

            track.draw_track((self.gridElementSize*column)+centerxOffset,(self.gridElementSize*row) + centeryOffset,self.image, self.tile_res, self.lineThickness, self.foregroundColor)
            column+=1
        #self.image = self.image.filter(SMOOTH_MORE)

    def draw_shape(self, blackPxSequence):

        step_count = self.maxRows
        row = 0
        column = 0
        blackPxLength = len(blackPxSequence)
        gridElementSize = self.width / self.maxRows
        y_start = 0
        y_end = self.image.height
        step_size = int(self.image.width / step_count)
        #for i in range(len(self.tracks)):
        j = 0
        for i in range(len(blackPxSequence)):
            if i < blackPxLength: 
                pixel = blackPxSequence[i]
                #print("drawing track " + str(i) + "at x:" + str(self.gridElementSize*pixel["y"]) + " y: " + str(self.gridElementSize*pixel["x"]))
                self.tracks[j].draw_track((self.gridElementSize*pixel["x"]),(self.gridElementSize*pixel["y"]),self.image, self.tile_res, self.lineThickness, self.foregroundColor)
            else:
                break
            j+=1
            if j >= len(self.tracks):
                if self.duplicateActivities == True:
                    j = 0
                else:
                    break
        
        
    def get_image(self):
        return(self.image)
    
    def get_max_track_width(self):
        maxWidth = 0
        for track in self.tracks:
            width = track.get_width()
            if (width > maxWidth):
                maxWidth = width
        #print("max width of track: " + str(maxWidth))
        return maxWidth
    
    def get_tracks_length(self):
        return(len(self.tracks))
        
        
            

    #activity. only stores GPX data at the moment. eventually should also have data such as activity name, time, distance, etc....          
class Track:
    def __init__(self, activity, min_lat, max_lat, min_lon, max_lon, zoom):
        """ constructor """
        self.activity = activity # list of coordinates
        x1, y1 = osm_lat_lon_to_x_y_tile (min_lat, min_lon, zoom)
        x2, y2 = osm_lat_lon_to_x_y_tile (max_lat, max_lon, zoom)
        self.x1 = min (x1, x2)
        self.x2 = max (x1, x2)
        self.y1 = min (y1, y2)
        self.y2 = max (y1, y2)
        self.width = (self.x2 - self.x1 + 1)
        self.height = (self.y2 - self.y1 + 1)
        self.zoom = zoom

    
        self.x_offset = 0
        self.y_offset = 0

        
    def lat_lon_to_image_xy (self, lat_deg, lon_deg, tile_res):
        """ Internal. Converts lat, lon into dst_img coordinates in pixels """
        lat_rad = math.radians(lat_deg)
        n = 2.0 ** self.zoom
        xtile_frac = (lon_deg + 180.0) / 360.0 * n
        ytile_frac = (1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n
        img_x = int( (xtile_frac-self.x1)*tile_res )
        img_y = int( (ytile_frac-self.y1)*tile_res )
        return (img_x + self.x_offset, img_y + self.y_offset) #modified with offsets +300

    def draw_track (self, new_x_offset, new_y_offset, image, tile_res, lineThickness, lineColor):
        
        self.x_offset = new_x_offset #(self.width*tile_res)/2 
        self.y_offset = new_y_offset 
        draw = pil_draw.Draw(image)

        x_from = 0
        y_from = 0
        linePointIdx = 0 #a line requires 2 points to draw. if this is 0, then it sets the first point, if this is 1, then it sets the second point
        
        for coordinate in self.activity:
            #coordinate[0] is latitude. coordinate[1] is longitude
            if (linePointIdx == 0):
                x_from, y_from = self.lat_lon_to_image_xy (coordinate[0], coordinate[1], tile_res) #set first coordinate
            else:    
                x_to, y_to = self.lat_lon_to_image_xy (coordinate[0], coordinate[1], tile_res)
                #draw.line ((x_from,y_from,x_to,y_to), (255,0,trk), 2)
                draw.line ((x_from ,y_from,x_to, y_to), lineColor, lineThickness) #coordinates, color, thickness
                x_from = x_to
                y_from = y_to
               
            linePointIdx +=1
        # (41.14569, -81.34207), (41.14564, -81.34187), (41.14556, -81.34178) 
            
    def get_width(self):
        return(self.width)
    def get_height(self):
        return(self.height)

def get_latlon_bounds(activity):
    min_lat = None
    max_lat = None
    min_lon = None
    max_lon = None

    for coordinate in activity:
        if min_lat is None or coordinate[0] < min_lat:
            min_lat = coordinate[0]
        if max_lat is None or coordinate[0] > max_lat:
            max_lat = coordinate[0]
        if min_lon is None or coordinate[1] < min_lon:
            min_lon = coordinate[1]
        if max_lon is None or coordinate[1] > max_lon:
            max_lon = coordinate[1]

    if min_lat and max_lat and min_lon and max_lon:
        return (min_lat, max_lat, min_lon, max_lon)
    return None

def gpx_to_list(gpx):
    activity = []
    for gpxTrack in gpx.tracks:
        for segment in gpxTrack.segments:
            for point in segment.points:
                activity.append((point.latitude,point.longitude))
    return(activity)
            


def getVis(data, lineThickness = 5, backgroundColor = (255,255,255), backgroundImage = "", backgroundBlur = 5, foregroundColor = (0,0,0), gridOn = False, gridColor = (0,0,0), gridThickness = 1,  title = "", silhouetteImage = "", duplicateActivities = False, textBackgroundFade = False, infoText = False, totalTime = "", totalDistance = ""): 
    print("sil image: " + silhouetteImage)
    ### Un-comment these when Adam has fixed font/image dependencies
    infoText = (infoText == "on")
    textBackgroundFade = (textBackgroundFade == "on")
    duplicateActivities = (duplicateActivities == "on")
    ###
    tracks = [] #list to store activities
    #####POLYLINE LIST####
    if (type(data[0][0]) is tuple): #very rough way to check if it is a polyline list or a GPX file
        for activity in data:
            try:
                min_lat, max_lat, min_lon, max_lon = get_latlon_bounds(activity)
                #print(get_latlon_bounds(activity))
                zoom = osm_get_auto_zoom_level (min_lat, max_lat, min_lon, max_lon, 1)
                track = Track(activity, min_lat, max_lat, min_lon, max_lon, zoom)
                tracks.append(track)
            except Exception as e:
                logging.exception(e)
                print("Error processing polyline")
                sys.exit(1)
                
    #####GPX FILE#####
    ##convert GPX file to list
    else:
        print("GPX File")
        dir = "uploads/" + data + "/*.gpx"
        gpx_files = glob.glob("uploads/" + data + "/*.gpx") #get all GPX files in user upload directory
        
        for gpx_file in gpx_files:

            try:
                gpx = gpxpy.parse(open(gpx_file))
                
                #start_time, end_time = gpx.get_time_bounds()
                #min_lat, max_lat, min_lon, max_lon = gpx.get_bounds()
                
                activity = gpx_to_list(gpx)
                min_lat, max_lat, min_lon, max_lon = get_latlon_bounds(activity)
                zoom = osm_get_auto_zoom_level (min_lat, max_lat, min_lon, max_lon, 1)
                track = Track(activity, min_lat, max_lat, min_lon, max_lon, zoom)
                tracks.append(track)

            except Exception as e:

                logging.exception(e)
                print('Error processing: %s' % gpx_file)
                continue

    ##if a silhouetteImage is provided, then the activities should be drawn in the shape of said silhouetteImage. else it should be drawn in a grid. somewhat messy and could be cleaned up
    if silhouetteImage != "":
        silhouetteImage = pil_image.open("static/silhouette-images/"+silhouetteImage)
        if silhouetteImage.is_animated:
            images = []
            count = 1
            for frameNum in range(0,silhouetteImage.n_frames):
                silhouetteImage.seek(frameNum)
                print("frame " + str(count) + "/" + str(silhouetteImage.n_frames))
                count+=1
                image_creator = ImageCreator(tracks, lineThickness, backgroundColor, backgroundImage, backgroundBlur, foregroundColor, gridOn, gridColor, gridThickness,  title, silhouetteImage, duplicateActivities, textBackgroundFade, infoText, totalTime, totalDistance)
                blackPixels = get_black_pixels(silhouetteImage, True)
                #print("number of black pixels: " + str(len(blackPixels)))
                image_creator.draw_shape(blackPixels)
                image_creator.draw_overlay()
                #image_creator.get_image().show()
                images.append(image_creator.get_image())
                del image_creator
                #if(count>10): break
            drawnImage = images[0].save('testGif3.gif',save_all=True, append_images=images[1:])
            return

        else:

            image_creator = ImageCreator(tracks, lineThickness, backgroundColor, backgroundImage, backgroundBlur, foregroundColor, gridOn, gridColor, gridThickness,  title, silhouetteImage, duplicateActivities, textBackgroundFade, infoText, totalTime, totalDistance)
            blackPixels = get_black_pixels(silhouetteImage, False)
            image_creator.draw_shape(blackPixels)
            image_creator.draw_overlay()
            drawnImage = save_image(image_creator.get_image())
            
            
    ##draw activities as facets (grid formation)
    else:
        image_creator = ImageCreator(tracks, lineThickness, backgroundColor, backgroundImage, backgroundBlur, foregroundColor, gridOn, gridColor, gridThickness,  title, None,duplicateActivities, textBackgroundFade, infoText, totalTime, totalDistance)
        image_creator.draw_facets()
        image_creator.draw_overlay()
        drawnImage = save_image(image_creator.get_image())

    image_creator.image.close()
    if hasattr(image_creator, "backgroundImageFilePath"):
        os.remove(image_creator.backgroundImageFilePath) 

    # Delete GPX files
    if type(data) is str:
        if os.path.exists("uploads/" + data):
            shutil.rmtree("uploads/" + data)

    return drawnImage

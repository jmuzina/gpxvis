

import sys  
import math 
import logging 
import urllib
import os 
import gpxpy 
from PIL import Image as pil_image
from PIL import ImageDraw as pil_draw

#resolution of drawn tracks
osm_tile_res = 65

def format_time(time_s):
    if not time_s:
        return 'n/a'
    minutes = math.floor(time_s / 60.)
    hours = math.floor(minutes / 60.)
    return '%s:%s:%s' % (str(int(hours)).zfill(2), str(int(minutes % 60)).zfill(2), str(int(time_s % 60)).zfill(2)) 

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


##this class is the canvas that the activities(tracks) will be drawn on.
class ImageCreator:
    def __init__(self, tracks):
        #print(tracks)
        self.tracks = tracks
        self.width = 10000
        self.height = 10000
        self.image = pil_image.new ("RGB", (self.width, self.height), (255,255,255))
        
    def draw_facets(self):
        row = 0
        maxRows = 10
        column = 0
        gridSize = 1000
        for track in self.tracks:
            if column == maxRows:
                row+=1
                column = 0
            track.draw_track(0+gridSize*column,0+gridSize*row,self.image)
            column+=1
            
    def save_image(self, filename):
        #print("Saving " + filename) 
        self.image.save (filename)
        self.image.show()
        
    def draw_grid(self):
        step_count = 10
        # Draw some lines
        draw = pil_draw.Draw (self.image)
        y_start = 0
        y_end = self.image.height
        step_size = int(self.image.width / step_count)
        for x in range(0, self.image.width, step_size):
            line = ((x, y_start), (x, y_end))
            draw.line(line, fill=128)
        x_start = 0
        x_end = self.image.width
        for y in range(0, self.image.height, step_size):
            line = ((x_start, y), (x_end, y))
            draw.line(line, fill=128)
        del draw
    

#activity. only stores GPX data at the moment. eventually should also have data such as activity name, time, distance, etc....          
class Track:
    def __init__(self, gpx, min_lat, max_lat, min_lon, max_lon, zoom):
        """ constructor """
        self.gpx = gpx
        x1, y1 = osm_lat_lon_to_x_y_tile (min_lat, min_lon, zoom)
        x2, y2 = osm_lat_lon_to_x_y_tile (max_lat, max_lon, zoom)
        self.x1 = min (x1, x2)
        self.x2 = max (x1, x2)
        self.y1 = min (y1, y2)
        self.y2 = max (y1, y2)
        self.width = (self.x2 - self.x1 + 1) * osm_tile_res
        self.height = (self.y2 - self.y1 + 1) * osm_tile_res
        self.zoom = zoom
        
        #print (self.width, self.height)
    
        self.x_offset = 0
        self.y_offset = 0

        
    def lat_lon_to_image_xy (self, lat_deg, lon_deg):
        """ Internal. Converts lat, lon into dst_img coordinates in pixels """
        lat_rad = math.radians(lat_deg)
        n = 2.0 ** self.zoom
        xtile_frac = (lon_deg + 180.0) / 360.0 * n
        ytile_frac = (1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n
        img_x = int( (xtile_frac-self.x1)*osm_tile_res )
        img_y = int( (ytile_frac-self.y1)*osm_tile_res )
        return (img_x + self.x_offset + 300, img_y + self.y_offset+ 300) #modified with offsets

    def draw_track (self, new_x_offset, new_y_offset, image):
        
        self.x_offset = new_x_offset
        self.y_offset = new_y_offset 
        draw = pil_draw.Draw (image)
        
        for gpxTrack in self.gpx.tracks:
            for segment in gpxTrack.segments:
                idx = 0
                x_from = 0
                y_from = 0
                for point in segment.points:
                    if (idx == 0):
                        x_from, y_from = self.lat_lon_to_image_xy (point.latitude, point.longitude)
                    else:
                        x_to, y_to = self.lat_lon_to_image_xy (point.latitude, point.longitude, )
#                        draw.line ((x_from,y_from,x_to,y_to), (255,0,trk), 2)
                        draw.line ((x_from,y_from,x_to,y_to), (0,0,0), 15) #coordinates, color, thickness
                        x_from = x_to
                        y_from = y_to
                    idx += 1
    
def getVis(gpxXMLs):
    tracks = []
    for xml in gpxXMLs:
        #print("------visualizing---------\n\n", xml)
        try:
            gpx = gpxpy.parse(xml)
            start_time, end_time = gpx.get_time_bounds()
            min_lat, max_lat, min_lon, max_lon = gpx.get_bounds()
            zoom = osm_get_auto_zoom_level (min_lat, max_lat, min_lon, max_lon, 6)

            # Print track stats
            #print ('--------------------------------------------------------------------------------')
            #print ('  GPX file     : %s' % gpx_file)
            #print('  Started       : %s' % start_time)
            #print('  Ended         : %s' % end_time)
            #print('  Length        : %2.2fkm' % (gpx.length_3d() / 1000.))
            #moving_time, stopped_time, moving_distance, stopped_distance, max_speed = gpx.get_moving_data()
            #print('  Moving time   : %s' % format_time(moving_time))
            #print('  Stopped time  : %s' % format_time(stopped_time))
#           # print('  Max speed     : %2.2fm/s = %2.2fkm/h' % (max_speed, max_speed * 60. ** 2 / 1000.))    
            #uphill, downhill = gpx.get_uphill_downhill()
            #print('  Total uphill  : %4.0fm' % uphill)
            #print('  Total downhill: %4.0fm' % downhill)
            #print('min_lat: ' + str(min_lat))
            #print("  Bounds        : [%1.4f,%1.4f,%1.4f,%1.4f]" % (min_lat, max_lat, min_lon, max_lon))
            #print("zoom: " + str(zoom))
            #print("  Zoom Level    : %d" % z)

            track = Track(gpx, min_lat, max_lat, min_lon, max_lon, zoom)
            tracks.append(track)

        except Exception as e:

            logging.exception(e)
            print('Error processing: ')
            sys.exit(1)
    
    image_creator = ImageCreator(tracks)
    #image_creator.draw_grid() #useful for debugging and positioning
    image_creator.draw_facets()
    image_creator.save_image('facets' + '.png')
    print("saved img")

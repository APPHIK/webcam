import os
import shodan
import requests
import socket
import urllib
from PIL import Image, ImageEnhance
from rich import print
from clarifai.rest import ClarifaiApp

class Scanner(object):
    def __init__(self):
        socket.setdefaulttimeout(5)
        self.SHODAN_API_KEY = os.environ.get("SHODAN_API_KEY")
        assert self.SHODAN_API_KEY != ""
        self.api = shodan.Shodan(self.SHODAN_API_KEY)
        # preset url schemes
        self.default_url_scheme = "[link=http://{ip}:{port}][i][green]{ip}[/green]:[red]{port}[/red][/link]"
        self.MJPG_url_scheme = "[link=http://{ip}:{port}/?action=stream][i]http://[green]{ip}[/green]:[red]{port}[/red]" \
                               "[blue]/?action=stream[/blue][/link]"
        self.clarifai_initialized = False

    def init_clarifai(self):
        self.CLARIFAI_API_KEY = os.environ.get("CLARIFAI_API_KEY")
        assert self.CLARIFAI_API_KEY != ""
        self.clarifai_app = ClarifaiApp(api_key='ac61aa2283a04f54bffb59bbae86206e')
        self.clarifai_model = self.clarifai_app.public_models.general_model
        self.clarifai_initialized = True

    def tag_image(self,url):
        response = self.clarifai_model.predict_by_url(url=url)
        results = [concept['name'] for concept in response['outputs'][0]['data']['concepts']]
        return results

    def check_empty(self,image_source,tolerance=5)->bool:
        im_loc = ".tmpimage"
        urllib.request.urlretrieve(image_source, im_loc)
        im = Image.open(im_loc)
        extrema = im.convert("L").getextrema()
        if abs(extrema[0]-extrema[1]) <= tolerance:
            return False
        return True

    def scan(self, camera_type, url_scheme = '', check_empty_url='',check_empty = True, tag=False):
        if url_scheme == '':
            url_scheme = self.default_url_scheme

        if tag and (not self.clarifai_initialized):
            self.init_clarifai()

        results = self.api.search("webcams")
        max_time = len(results["matches"])*10
        print(f"maximum time:{max_time} seconds")
        for result in results["matches"]:
            if camera_type in result["data"]:
                url = f"http://{result['ip_str']}:{result['port']}"
                try:
                    r = requests.get(url, timeout=5)
                    if r.status_code == 200:
                        if check_empty == False:
                            print(
                                url_scheme.format(ip=result['ip_str'], port=result['port'])
                            )
                            continue
                        if self.check_empty(check_empty_url.format(url=url)):
                            print(
                                url_scheme.format(ip=result['ip_str'], port=result['port'])
                            )
                            if tag:
                                for t in self.tag_image(check_empty_url.format(url=url)):
                                    print(f"[green]{t}[/green]",end=" ")
                                print()
                except:
                    continue

    def MJPG(self,check,tag):
        scheme = self.MJPG_url_scheme
        if check:
            self.scan("MJPG-streamer", url_scheme=scheme, check_empty_url="{url}/?action=snapshot",tag=tag)
        else:
            self.scan("MJPG-streamer", url_scheme=scheme, check_empty_url="{url}/?action=snapshot",tag=tag)

    def webcamXP(self,check,tag):
        if check:
            self.scan("webcamXP", check_empty_url='{url}/cam_1.jpg', tag=tag)
        else:
            self.scan("webcamXP",check_empty_url='{url}/cam_1.jpg',tag=tag)
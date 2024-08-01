from mayavi import mlab
from PIL import Image
from pyvirtualdisplay import Display
from typing import TypedDict
import utils.gcodeParser as gcode

# Types definition
Color = tuple[float, float, float]
Points = TypedDict("Points", {"x": list[float], "y": list[float], "z": list[float]})
Coordinates = TypedDict(
    "Coordinates", {"object": Points, "moves": Points}
)


class GcodeRenderer:
    def __init__(self):
        self.imgwidth = 800
        self.imgheight = 600

        self.path = ""
        self.moves = False

        self.coords: Coordinates = {}
        self.coords["object"] = {}
        self.coords["moves"] = {}
        self.coords["object"]["x"] = []
        self.coords["object"]["y"] = []
        self.coords["object"]["z"] = []
        self.coords["moves"]["x"] = []
        self.coords["moves"]["y"] = []
        self.coords["moves"]["z"] = []

        self.bedsize = [210, 210]
        red = (1, 0, 0)
        blue = (0, 0.4980, 0.9960)

        self.extrudecolor: Color = blue
        self.movecolor: Color = red

        # Virtual display configuration
        display = Display(visible=False, size=(1280, 1024))
        display.start()
        mlab.options.offscreen = True

    def run(self, path_src: str, path_out: str, moves: bool):
        self.path = path_src
        self.moves = moves

        self.createScene()
        self.loadModel(self.path)
        self.plotModel()
        self.save(path_out)

    def loadModel(self, path: str):
        parser = gcode.GcodeParser()
        model = parser.parseFile(path)

        for seg in model.segments:
            if seg.type == "G1":
                self.coords["object"]["x"].append(seg.coords["x"])
                self.coords["object"]["y"].append(seg.coords["y"])
                self.coords["object"]["z"].append(seg.coords["z"])
                continue

            if self.moves:
                self.coords["moves"]["x"].append(seg.coords["x"])
                self.coords["moves"]["y"].append(seg.coords["y"])
                self.coords["moves"]["z"].append(seg.coords["z"])

    def createScene(self):
        fig1 = mlab.figure(bgcolor=(1, 1, 1), size=(self.imgwidth, self.imgheight))
        fig1.scene.parallel_projection = False
        fig1.scene.render_window.point_smoothing = False
        fig1.scene.render_window.line_smoothing = False
        fig1.scene.render_window.polygon_smoothing = False
        fig1.scene.render_window.multi_samples = 8

    def plotModel(self):
        mlab.plot3d(
            self.coords["object"]["x"],
            self.coords["object"]["y"],
            self.coords["object"]["z"],
            color=self.extrudecolor,
            line_width=2.0,
            representation="wireframe",
        )
        if len(self.coords["moves"]["x"]) > 0:
            mlab.plot3d(
                self.coords["moves"]["x"],
                self.coords["moves"]["y"],
                self.coords["moves"]["z"],
                color=self.movecolor,
                line_width=2.0,
                representation="wireframe",
            )

    def save(self, path_out: str):
        mlab.view(320, 70)
        mlab.view(distance=20)
        mlab.view(focalpoint=(self.bedsize[0] / 2, self.bedsize[1] / 2, 20))
        mlab.savefig(path_out, size=(800, 600))
        mlab.close(all=True)
        basewidth = 800
        img = Image.open(path_out)
        wpercent = basewidth / float(img.size[0])
        hsize = int((float(img.size[1]) * float(wpercent)))
        img = img.resize((basewidth, hsize))
        img.save(path_out)

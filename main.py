from flask import Flask, send_file, send_from_directory, request
from flask_restful import Api, Resource
from time import sleep

import barcode
from barcode.writer import ImageWriter

import qrcode

from PIL import Image

app = Flask(__name__)
api = Api(app)


def add_margin(pil_img, margins, color = (255, 255, 255)):
    width, height = pil_img.size
    new_width = width + margins[3] + margins[1]
    new_height = height + margins[0] + margins[2]
    result = Image.new(pil_img.mode, (new_width, new_height), color)
    result.paste(pil_img, (margins[3], margins[0]))
    return result

class Barcode(Resource):
    def get(self, type, data):
        try:
            #Check Type
            if type != 'ean8' and type != 'code128' and type != 'code39':
                print("Error-Type must be ean8, code128, or code39. You entered: " + type)
                return {"Error":"Type must be ean8, code128, or code39. You entered: " + type}    
            # Set the class based on the type from the request
            bc_class = barcode.get_barcode_class(type)
            # Generate the barcode
            bc_data = bc_class(data, writer=ImageWriter())
            # Save the image
            img = bc_data.save("imgs/" + data)
            # Open the image as a Pillow image object
            im = Image.open(img)
            width, height = im.size
            # Crop the margin, so the image is just the barcode
            im = im.crop((30, 11, width - 30, 189))

            # Get optional params from the request url
            new_width = request.args.get('width')
            new_height = request.args.get('height')
            margin_x = request.args.get('margin_x')
            margin_y = request.args.get('margin_y')
            margin_top = request.args.get('margin_top')
            margin_right = request.args.get('margin_right')
            margin_bottom = request.args.get('margin_bottom')
            margin_left = request.args.get('margin_left')

            dims = [im.size[0], im.size[1]]
            if new_width is not None:
                dims[0] = int(new_width)
            if new_height is not None:
                dims[1] = int(new_height)
            
            # Load margins (more specific overrides more generic)
            #   i.e. if margin_x is 20 and margin_right is 30, 
            #       then the left margin will be 20 
            #       and the right margin will be 30
            margins = [10, 20, 10, 20]
            if margin_x is not None:
                margins[1] = int(margin_x)
                margins[3] = int(margin_x)
            if margin_y is not None:
                margins[0] = int(margin_y)
                margins[2] = int(margin_y)
            if margin_top is not None:
                margins[0] = int(margin_top)
            if margin_right is not None:
                margins[1] = int(margin_right)
            if margin_bottom is not None:
                margins[2] = int(margin_bottom)
            if margin_left is not None:
                margins[3] = int(margin_left)

            # Resize to specified size based on request
            im = im.resize(tuple(dims))
            im = add_margin(im, margins)
            # Save the adjusted image

            im.save(img)
        except:
            # If there is an error, then return the error image
            img = "error.png"

        # Return the image
        return send_file(img, mimetype='image/png')

class Status(Resource):
    def get(self):
        return {"Status":"Running"}

#Test Comment
class QRCode(Resource):
    def get(self, name):
        try:
            url = request.full_path
            data = url[url.find("data=") + 5:]
            # Get data from url parameter
            linkTo = "#" + request.args.get('linkTo', default="")

            # Establish path
            img = "imgs/" + name + ".png" 

            # Set QR code parameters
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            # Add data
            qr.add_data(data + linkTo)
            
            # Generate QR Code
            qr.make(fit=True)
            im = qr.make_image(fill_color="black", back_color="white")
            im.save(img)
        except:
            img = "error.png"
            
        return send_file(img, mimetype='image/png')
        
        
    
# Method to get a file from a specific file path (used with AO Attachments)
class GetFile(Resource):
    def get(self):
        path = "/Volumes/Pacific-Lock/"
        filePath = request.args.get('path')
        return send_from_directory(path, filePath)


api.add_resource(Status, "/")
api.add_resource(Barcode, "/barcode/<string:type>/<string:data>")
api.add_resource(QRCode, "/qrcode/<string:name>")
api.add_resource(GetFile, "/getFile")

# Starts server
# Add ", debug=True" to run in debug mode
if __name__ == "__main__":
    app.run(host="localhost", port=8000)
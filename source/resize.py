#!/usr/bin/env python3

from collections import namedtuple
from dataclasses import dataclass
from enum import Enum
from glob import glob
from os import listdir
from os.path import abspath
from os.path import isdir
from os.path import isfile
from os.path import join
from os.path import splitext
from re import search
from sys import argv
from sys import exit
from typing import Callable

from PIL import Image

HELP = '''Usage: resize 'height' | 'width'  length  files | directory

Batch resizes images to a given height or width.
Resizes any image files in the given directory or files.

Arguments:

    'height' | 'width'     The resize operation to perform.
    length                 The length in pixels to resize to.
    files | directory      The files or directory to resize.

Example:

    resize height 1080 *.png
'''

IMAGE_EXTENSIONS = ['gif', 'jpg', 'jpeg', 'png', 'webp']


## Utils ###################################################

def argument(n, default = ''):
    ''' Returns the command line parameter
        or the default if it does not exist.
    '''
    if len(argv) > n:
        return argv[n]
    return default

def arguments():
    return argv[1:]

def find_number_in_list(items, default = None):
    for item in items:
        if item.isdigit():
            return item
    return default

def find_match_in_list(items, match_dict, default = None):
    for item in items:
        if item.lower() in match_dict:
            return item
    return default

def get_number_and_remainder(items, default = None):
    return to_int_and_remainder(
            *item_and_remainder(find_number_in_list(items), items))

def get_match_and_remainder(items, match_dict, default = None):
    return to_match_and_remainder(
            *item_and_remainder(find_match_in_list(items, match_dict, default), items),
            match_dict)

def item_and_remainder(item, items):
    if item is None:
        return item, items
    items.remove(item)
    return item, items

def nl():
    ''' Quick, less noisy version of print() '''
    print()

def no_arguments():
    ''' Returns True if there are
        no command line parameters
    '''
    return len(argv) <= 1

def not_enough_arguments(expected):
    return len(argv) <= expected

def show_error_and_exit(message):
    print
    nl()
    exit(1)

def show_help():
    print(HELP)

def to_int_and_remainder(item, items):
    if item is None:
        return item, items
    return int(item), items

def to_match_and_remainder(item, items, match_dict):
    if item is None:
        return item, items
    return match_dict[item], items


## Directory ###############################################

def resize_name(path):
    return path.removesuffix('.' + extension(path)) + ' - resized.' + extension(path)

def extension(name):
    ''' Returns the extension of a file.
        Returns as lower case.
        Does not return the '.'.
    '''
    if '.' in name:
        return (splitext(name)[1])[1:].lower()
    return ''

def is_image(name):
    return extension(name) in IMAGE_EXTENSIONS

def read_files(path):
    ''' Reads the files in the directory '''
    if isdir(path):
        return [ join(path, name) for name in 
            filter(
                lambda file: isfile(join(path, file)),
                listdir(path)) ]
    return glob(path)

def read_image_files(path):
    ''' Reads the directory
        but returns image files only.
    '''
    return [ name for name in read_files(path) if is_image(name)]


## Image Calculations ######################################

Size = namedtuple("Size", ["width", "height"])


def height_ratio(size_1, size_2):
    ''' Calculates the height ratios of 2 sizes.'''
    return ratio(size_2.height, size_1.height)

def ratio(length_1, length_2):
    ''' Calculates the ratio of 2 numbers.'''
    return length_1 / length_2

def resize_height(image, width):
    ''' Calculates the new height of an image
        given the new width.
    '''
    size = to_size(image)
    return int(ratio(width, size.width) * size.height)

def resize_width(image, height):
    ''' Calculates the new width of an image
        given the new height.
    '''
    size = to_size(image)
    return int(ratio(height, size.height) * size.width)

def to_height(image, height):
    ''' Returns the size of an image
        fitted to a given height.
    '''
    return Size(resize_width(image, height), height)
    
def to_size(image):
    ''' Returns the size as Type Size for the image.'''
    return Size(*image.size)

def to_width(image, width):
    ''' Returns the size of an image
        fitted to a given width.
    '''
    return Size(width, resize_height(image, width))

def width_ratio(size_1, size_2):
    ''' Calculates the width ratios of 2 sizes.'''
    return ratio(size_2.width, size_1.width)

def within_size(image, max_size):
    ''' Returns the size of the image
        resized to fit into max_size.
        
        The size with the smallest ratio
        determines the best fit.
    '''
    image_size = to_size(image)

    if height_ratio(image_size, max_size) <= width_ratio(image_size, max_size):
        return to_height(image, max_size.height)

    return to_width(image, max_size.width)
        

## Image Operations ########################################

def resize_to_height(path, height):
    image = Image.open(path)
    resized = image.resize(to_height(image, height), Image.LANCZOS)
    resized.save(resize_name(path))

def resize_to_width(path, width):
    image = Image.open(path)
    resized = image.resize(to_width(image, width), Image.LANCZOS)
    resized.save(resize_name(path))

def resize_within(path, size):
    image = Image.open(path)
    resized = image.resize(within_size(image, size), Image.LANCZOS)
    resized.save(resize_name(path))

def resize_image(settings, file):
    print(file)
    resize = settings.operation.function
    resize(file, settings.length)

def resize_images(settings):
    ''' Reads in the directory images
        and resizes them to the given height.
    '''

    print(f'Resizing to {settings.operation.name} {settings.length}...' + '\n')

    for file in read_image_files(settings.directory):
        resize_image(settings, file)

    print('\n' + 'Done.' + '\n')


## Settings ################################################

@dataclass
class Operation:
    name: str
    function: Callable

@dataclass
class Settings:
    operation: Operation
    length: int
    directory: str

EXPECTED_ARGUMENT_COUNT = 3

HEIGHT_OPERATION = Operation('height', resize_to_height)
WIDTH_OPERATION = Operation('width', resize_to_width)

OPERATION_ARGUMENTS = {
    'h': HEIGHT_OPERATION,
    'height': HEIGHT_OPERATION,
    'w': WIDTH_OPERATION,
    'width': WIDTH_OPERATION
}

def get_length(arguments):
    return get_number_and_remainder(arguments, None)

def get_operation(arguments):
    return get_match_and_remainder(arguments, OPERATION_ARGUMENTS, None)

def to_settings(arguments):
    operation, remainder = get_operation(arguments)
    length, remainder = get_length(remainder)
    return Settings(operation, length, abspath(remainder[0]))

def validate_settings(settings):
    if not settings.operation:
        show_error_and_exit("Missing 'height' or 'width'.")
    if not settings.length:
        show_error_and_exit("Missing resize length.")


## Main ####################################################

def main():
    settings = to_settings(arguments())
    validate_settings(settings)
    resize_images(settings)

nl()

if not_enough_arguments(EXPECTED_ARGUMENT_COUNT):
    show_help()
    exit()

main()

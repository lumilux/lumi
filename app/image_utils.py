import os

from PIL import Image, ImageOps

def save_to_dir(image, orig_path, other_dir, quality, profile):
    orig_dir, orig_file = os.path.split(orig_path)
    image_dir, _ = os.path.split(orig_dir)
    new_path = os.path.join(image_dir, other_dir, orig_file)
    image.save(new_path, quality=quality, icc_profile=profile)
    return new_path

def fit_and_save(temp_path, size=2400):
    photo_size = (size, size)
    photo = Image.open(temp_path)
    profile = photo.info.get('icc_profile')
    photo.thumbnail(photo_size, Image.ANTIALIAS)
    width, height = photo.size
    return (save_to_dir(photo, temp_path, 'photo', 90, profile), width, height)

def generate_thumbnail(photo_path, size=100):
    thumbnail_size = (size, size)
    photo = Image.open(photo_path)
    profile = photo.info.get('icc_profile')
    thumbnail = ImageOps.fit(photo, thumbnail_size, Image.ANTIALIAS)
    return save_to_dir(thumbnail, photo_path, 'thumb', 80, profile)

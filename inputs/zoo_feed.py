import time
from inputs.base import BaseFeed

class ZooFeed(BaseFeed):
    def __init__(self):
        self.cams = [
            {
                'id': 'zoo_panda_smithsonian',
                'name': 'Smithsonian National Zoo — Panda Cam',
                'nearby': 'Giant Panda Habitat',
                'img_url': 'https://images.unsplash.com/photo-1564349683136-77e08dba1ef7?w=800&auto=format&fit=crop&q=80',
                'youtube_id': 'NqOmHpwMUxs',
                'county': 'Washington DC',
                'route': 'Zone A',
                'direction': 'Habitat View',
                'latitude': 38.9296,
                'longitude': -77.0502
            },
            {
                'id': 'zoo_elephant_houston',
                'name': 'Houston Zoo — Elephant Habitat Cam',
                'nearby': 'Asian Elephant Yard',
                'img_url': 'https://images.unsplash.com/photo-1557050543-4d5f4e07ef46?w=800&auto=format&fit=crop&q=80',
                'youtube_id': 'cTi5sCsUSfc',
                'county': 'Houston TX',
                'route': 'Zone B',
                'direction': 'Yard View',
                'latitude': 29.7159,
                'longitude': -95.3908
            },
            {
                'id': 'zoo_gorilla_houston',
                'name': 'Houston Zoo — Gorilla Habitat Cam',
                'nearby': 'Gorilla Habitat',
                'img_url': 'https://images.unsplash.com/photo-1540573133985-87b6da6d54a9?w=800&auto=format&fit=crop&q=80',
                'youtube_id': 'PcAOecvAh1U',
                'county': 'Houston TX',
                'route': 'Zone B',
                'direction': 'Habitat View',
                'latitude': 29.7162,
                'longitude': -95.3912
            },
            {
                'id': 'zoo_penguin_sandiego',
                'name': 'San Diego Zoo — Penguin Cam',
                'nearby': 'Conrad Prebys Africa Rocks',
                'img_url': 'https://images.unsplash.com/photo-1517783999520-f068d7431a60?w=800&auto=format&fit=crop&q=80',
                'youtube_id': '1NoSs03ZrlY',
                'county': 'San Diego CA',
                'route': 'Zone C',
                'direction': 'Pool View',
                'latitude': 32.7353,
                'longitude': -117.1490
            },
            {
                'id': 'zoo_lion_smithsonian',
                'name': 'Smithsonian National Zoo — Lion Cam',
                'nearby': 'Great Cats Habitat',
                'img_url': 'https://images.unsplash.com/photo-1546182990-dffeafbe841d?w=800&auto=format&fit=crop&q=80',
                'youtube_id': None,
                'county': 'Washington DC',
                'route': 'Zone A',
                'direction': 'Outdoor Yard',
                'latitude': 38.9300,
                'longitude': -77.0508
            },
            {
                'id': 'zoo_grizzly_oakland',
                'name': 'Oakland Zoo — Grizzly Bear Cam',
                'nearby': 'California Trail',
                'img_url': 'https://images.unsplash.com/photo-1508817628294-5a453fa0b8fb?w=800&auto=format&fit=crop&q=80',
                'youtube_id': None,
                'county': 'Oakland CA',
                'route': 'Zone D',
                'direction': 'Trail View',
                'latitude': 37.7711,
                'longitude': -122.1765
            },
            {
                'id': 'zoo_penguin_pittsburgh',
                'name': 'Penguin Cam Live (Pittsburgh Zoo)',
                'nearby': 'Penguin Pool',
                'img_url': 'https://images.unsplash.com/photo-1517783999520-f068d7431a60?w=800&auto=format&fit=crop&q=80',
                'youtube_id': 'cTi5sCsUSfc',
                'county': 'Pittsburgh Zoo',
                'route': 'Zone D',
                'direction': 'Underwater View',
                'latitude': 32.7348,
                'longitude': -117.1512,
                'is_youtube': True
            }
        ]

    def get_devices(self):
        # Zoo feeds are static mock devices but represent active cameras
        return self.cams

    def get_latest_frame(self, device_id):
        for cam in self.cams:
            if cam['id'] == device_id:
                return cam['img_url']
        return None

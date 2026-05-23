import time
from inputs.base import BaseFeed

class ZooFeed(BaseFeed):
    def __init__(self):
        # We will use high-quality animal images to represent "live streams"
        self.cams = [
            {
                'id': 'zoo_panda',
                'name': 'Panda Sanctuary Cam 1',
                'nearby': 'Bamboo Grove',
                'img_url': 'https://images.unsplash.com/photo-1564349683136-77e08dba1ef7?w=800&auto=format&fit=crop&q=80',
                'county': 'Zoo North',
                'route': 'Zone A',
                'direction': 'East View',
                'latitude': 32.7355,
                'longitude': -117.1500
            },
            {
                'id': 'zoo_tiger',
                'name': 'Tiger Canyon Cam',
                'nearby': 'Waterfalls Overlook',
                'img_url': 'https://images.unsplash.com/photo-1508817628294-5a453fa0b8fb?w=800&auto=format&fit=crop&q=80',
                'county': 'Zoo East',
                'route': 'Zone B',
                'direction': 'South View',
                'latitude': 32.7360,
                'longitude': -117.1480
            },
            {
                'id': 'zoo_elephant',
                'name': 'Elephant Savanna Cam 2',
                'nearby': 'Waterhole',
                'img_url': 'https://images.unsplash.com/photo-1557050543-4d5f4e07ef46?w=800&auto=format&fit=crop&q=80',
                'county': 'Zoo South',
                'route': 'Zone C',
                'direction': 'North View',
                'latitude': 32.7340,
                'longitude': -117.1495
            },
            {
                'id': 'zoo_penguin',
                'name': 'Penguin Coast Active Cam',
                'nearby': 'Ice Pool',
                'img_url': 'https://images.unsplash.com/photo-1517783999520-f068d7431a60?w=800&auto=format&fit=crop&q=80',
                'county': 'Zoo South',
                'route': 'Zone D',
                'direction': 'Underwater View',
                'latitude': 32.7345,
                'longitude': -117.1510
            },
            {
                'id': 'zoo_koala',
                'name': 'Koala Outback Cam',
                'nearby': 'Eucalyptus Forest',
                'img_url': 'https://images.unsplash.com/photo-1546182990-dffeafbe841d?w=800&auto=format&fit=crop&q=80',
                'county': 'Zoo West',
                'route': 'Zone A',
                'direction': 'Canopy View',
                'latitude': 32.7350,
                'longitude': -117.1520
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

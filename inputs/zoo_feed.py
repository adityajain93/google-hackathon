from inputs.base import BaseFeed

class ZooFeed(BaseFeed):
    def __init__(self):
        self.cams = [
            {
                'id': 'zoo_otter_seattle',
                'name': 'Seattle Aquarium — Sea Otter & Fur Seal Cam',
                'nearby': 'Marine Mammal Habitat',
                'img_url': 'https://images.unsplash.com/photo-1564349683136-77e08dba1ef7?w=800&auto=format&fit=crop&q=80',
                'youtube_id': 'NqOmHpwMUxs',
                'county': 'Seattle WA',
                'route': 'Zone A',
                'direction': 'Pool View',
                'latitude': 47.6063,
                'longitude': -122.3425,
                'is_youtube': True
            },
            {
                'id': 'zoo_penguin_pittsburgh',
                'name': 'Pittsburgh Zoo — Penguin Cam',
                'nearby': 'PPG Aquarium Penguin Pool',
                'img_url': 'https://images.unsplash.com/photo-1517783999520-f068d7431a60?w=800&auto=format&fit=crop&q=80',
                'youtube_id': 'cTi5sCsUSfc',
                'county': 'Pittsburgh PA',
                'route': 'Zone B',
                'direction': 'Pool View',
                'latitude': 40.4519,
                'longitude': -79.9220,
                'is_youtube': True
            },
            {
                'id': 'zoo_tiger_turpentine',
                'name': 'Turpentine Creek — Tiger Cam',
                'nearby': 'Big Cat Refuge',
                'img_url': 'https://images.unsplash.com/photo-1540573133985-87b6da6d54a9?w=800&auto=format&fit=crop&q=80',
                'youtube_id': 'PcAOecvAh1U',
                'county': 'Eureka Springs AR',
                'route': 'Zone C',
                'direction': 'Habitat View',
                'latitude': 36.4012,
                'longitude': -93.7185,
                'is_youtube': True
            },
            {
                'id': 'zoo_giraffe_greenville',
                'name': 'EarthCam — Giraffe Paddock Cam',
                'nearby': 'Giraffe Paddock, Greenville SC',
                'img_url': 'https://images.unsplash.com/photo-1557050543-4d5f4e07ef46?w=800&auto=format&fit=crop&q=80',
                'youtube_id': '1NoSs03ZrlY',
                'county': 'Greenville SC',
                'route': 'Zone D',
                'direction': 'Paddock View',
                'latitude': 34.8526,
                'longitude': -82.3940,
                'is_youtube': True
            },
        ]

    def get_devices(self):
        return self.cams

    def get_latest_frame(self, device_id):
        for cam in self.cams:
            if cam['id'] == device_id:
                if cam.get('youtube_id'):
                    return f"https://www.youtube.com/watch?v={cam['youtube_id']}"
                return cam['img_url']
        return None

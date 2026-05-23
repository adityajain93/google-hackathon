class BaseFeed:
    def get_devices(self):
        """
        Retrieves active devices/cameras for this feed.
        Returns a list of dictionaries with standardized fields:
        {
            'id': str,
            'name': str,
            'nearby': str,
            'img_url': str,
            'latitude': float,
            'longitude': float,
            ...
        }
        """
        raise NotImplementedError

    def get_latest_frame(self, device_id):
        """
        Returns the latest frame (image URL or binary data) for the device.
        """
        raise NotImplementedError

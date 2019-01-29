from .interface import *


class ICoordinatesQuery(Interface):
    def query_coordinates_by_name(self, name: str, *args, **kwargs) -> list:
        """Queries coordinates for an object with the given name.

        Args:
            name (str): Name of object to query coordinates for.

        Returns:
            (list) List of dictionaries with the following keys:
                - name: Name of object
                - ra: Right ascension [sexagesimal]
                - ra_d: Right ascension [degrees]
                - dec: Declination [sexagesimal]
                - dec_d: Declination [degrees]
        """
        raise NotImplementedError


__all__ = ['ICoordinatesQuery']

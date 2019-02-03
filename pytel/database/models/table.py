from sqlalchemy import func


class GetByNameMixin:
    @classmethod
    def get_by_name(cls, session, name):
        # query
        result = session.query(cls).filter(func.lower(cls.name) == name.lower()).all()
        if len(result) != 1:
            return None

        # object
        return result[0]


__all__= ['GetByNameMixin']

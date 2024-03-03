class DataPointsRouter:
    """
    A router to control all database operations on models name StudentProfile

    """

    route_model_labels = {"Schools", "Chapter", "Subjects", "Chapter"}
    
    def db_for_read(self, model, **hints):
        """
        Attempts to read auth and contenttypes models go to auth_db.
        """
        if model.__name__ in self.route_model_labels:
            return "mysql-master-db"
        return "default"

    def db_for_write(self, model, **hints):
        """
        Attempts to write auth and contenttypes models go to auth_db.
        """
        if model.__name__ in self.route_model_labels:
            return "mysql-master-db"
        return "default"

    
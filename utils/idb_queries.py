class IDB_Connections:
    def __init__(self, mongo):
        self.mongo = mongo

    # returns DB user object or None if nonexistent
    def get_user(self, pid):
        return self.mongo.db.users.find_one({'pid' : pid})

    # add record to tags table
    def add_img_tags(self, filename, tags, date):
        self.mongo.db.tags.insert( {'image_name': filename, 'tags': tags, 'date': date} )

    # save image file to DB
    def save_image(self, filename, image):
        self.mongo.save_file(filename, image)

    # add record to users table
    def create_user_record(self, pid, filename):
        self.mongo.db.users.insert({'pid' : pid, 'image_names': [filename]})

    # add image to existing user
    def add_image_to_user(self, user, filename):
        user['image_names'].append(filename)
        return self.mongo.db.users.save(user)

    # return image by filename
    def get_image(self, filename):
        return self.mongo.send_file(filename)
    
    # returns all PID's in DB
    def get_pids(self):
        return set([user['pid'] for user in self.mongo.db.users.find({})])
    
    # returns all image tags in DB
    def get_tags(self):
        tags = set()
        for image in self.mongo.db.tags.find({}):
            for tag in image['tags']:
                tags.add(tag)
        return tags

    # returns records with corresponding tags
    def images_by_tags(self, tags):
        return self.mongo.db.tags.find({'tags': {'$all': tags}})
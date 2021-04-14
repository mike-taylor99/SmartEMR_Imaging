import string

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
        self.mongo.db.users.save(user)

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

    # adds image record to collections (creates new user if new user)
    def add_image_record(self, pid, image, tags, date):
        user = self.get_user(pid)
        self.save_image(image.filename, image)
        self.add_img_tags(image.filename, tags, date)

        if user:
            self.add_image_to_user(user, image.filename)
        else:
            self.create_user_record(pid, image.filename)

    # process natural language query and return images
    def process_nlq(self, nlq):
        if not nlq:
            return []
        
        all_PIDs, all_tags = self.get_pids(), self.get_tags()

        table = str.maketrans('', '', string.punctuation)
        stripped = [w.translate(table) for w in nlq.split()]

        query_PIDs = [word for word in stripped if word in all_PIDs]
        query_tags = [word for word in stripped if word in all_tags]

        user_images = [image for user in query_PIDs for image in self.get_user(user)['image_names']]
        tag_images = [record['image_name'] for record in self.images_by_tags(query_tags)]

        if user_images and tag_images:
            return list(set(user_images).intersection(set(tag_images)))
        elif user_images:
            return user_images
        elif tag_images:
            return tag_images
        else:
            return []

    # regular querying method where parameters are passed
    def regq(self, pid, tags):
        if pid:
            user = self.get_user(pid)
        else:
            user = None

        if user:
            user_images = user['image_names']
        else:
            user_images = None

        if tags:
            tag_images = [record['image_name'] for record in self.images_by_tags(tags)]
        else:
            tag_images = None

        if user_images and tag_images:
            return [image for image in tag_images if image in user_images]
        elif user_images:
            return user_images
        elif tag_images:
            return tag_images
        else:
            return []

    def create_admin_acct(obj):
        self.mongo.db.accounts.insert(obj)
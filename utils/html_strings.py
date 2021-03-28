def upload_images():
    return '''
        <div>Upload Patient Images and Tags: <br>
            <form method="POST" action="/create" enctype="multipart/form-data">
                <label>Patiient ID:</label>
                <input typr="text" name="pid">
                <label>Tags:</label>
                <input typr="text" name="tags">
                <label>Date:</label>
                <input typr="text" name="date">
                <input type="file" name="image">
                <input type="submit">
                </form>
            </div>
    '''

def find_patient_img():
    return '''
        <div>Find Patient Images: <br>
            <form method="POST" action="/findprofile" enctype="multipart/form-data">
                <label>Patient ID:</label>
                <input typr="text" name="pid">
                <input type="submit">
                </form>
            </div>
    '''

def find_tagged_img():
    return '''
        <div>Find Images by Tag(s): <br>
            <form method="POST" action="/findtags" enctype="multipart/form-data">
                <label>Tags:</label>
                <input typr="text" name="tags">
                <input type="submit">
                </form>
            </div>
    '''

def ui_test():
    return '''
        <div>Web Service Connection Test: <br>
            <form method="POST" action="/findimages" enctype="multipart/form-data">
                <label>Patient ID:</label>
                <input typr="text" name="pid">
                <label>Tags:</label>
                <input typr="text" name="tags">
                <input type="submit">
                </form>
            </div>
    '''

def nl_test():
    return '''
        <div>NL Query Test: <br>
            <form method="POST" action="/processquery" enctype="multipart/form-data">
                <label>Query:</label>
                <input typr="text" name="query">
                <input type="submit">
                </form>
            </div>
    '''

def classifier_test():
    return '''
        <div> Upload Image (Classification): <br>
            <form method="POST" action="/classify" enctype="multipart/form-data">
                <label>Image:</label>
                <input type="file" name="image">
                <input type="submit">
                </form>
            </div>
    '''
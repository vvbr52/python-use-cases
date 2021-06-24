import zipfile

fantasy_zip = zipfile.ZipFile('C:\\Stories\\Fantasy\\archive.zip')
fantasy_zip.extractall('C:\\Library\\Stories\\Fantasy')

fantasy_zip.close()
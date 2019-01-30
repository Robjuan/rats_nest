from django.test import TestCase


# TODO (current): build tests

def load_test_data():
    from .models import csvDocument
    import os
    from django.conf import settings
    from django.core.files.uploadedfile import SimpleUploadedFile

    f = open(os.path.join(settings.PROJECT_ROOT, 'Rats_Nest_Sample_Data.csv'), 'rb')
    file = SimpleUploadedFile('test_Data.csv',f.read())
    f.close()

    return csvDocument.objects.create(your_team_name='test_Team',
                                      description='test_Description',
                                      file=file,
                                      season=2018,
                                      parsed=False)


class UaParserTests(TestCase):

    def test_conversion_dict_check_with_valid(self):
        from .ua_parser import check_conversion_dict

        test_dict = {}
        for x in range(1, 23):
            name = 'test_Player_'+str(x)
            test_dict[name] = x
        test_dict['Anonymous'] = -1

        test_pk = load_test_data().pk

        self.assertIs(check_conversion_dict(test_dict, test_pk), True)

from globus_cli.config import get_config_obj
from globus_cli.services.transfer import get_client as get_tc

from tests.framework.cli_testcase import write_test_config


def cleanup_bookmarks(tc):
    for bm in tc.bookmark_list():
        tc.delete_bookmark(bm['id'])


def main():
    conf = get_config_obj()
    stored_conf = conf['cli']
    write_test_config(conf)
    try:
        tc = get_tc()
        cleanup_bookmarks(tc)
    finally:
        conf['cli'] = stored_conf
        conf.write()


if __name__ == '__main__':
    main()

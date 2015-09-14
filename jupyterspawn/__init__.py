"""
juspawn - spawn a new compute container

Usage:
    juspawn (-h | --help)
    juspawn [options] [<volumedir>...]

Options:
    -h, --help          Show brief usage summary.
    -q, --quiet         Reduce logging verbosity.

    --ip=IP             Address to bind host port to. [default: localhost]

    --user=USER         Username inside container.
    --uid=UID           User id inside container.

    <volumedir>         Each directory in <volumedir> will appear in
                        ~/notebooks/ with the same basename.

"""
import getpass
import logging
import os
import socket
import sys
import time

import docopt
import docker

CONTAINER_IMAGE_REPO='rjw57/jupyter'

def main():
    sys.exit(_main())

def _main():
    opts = docopt.docopt(__doc__)
    logging.basicConfig(
        level=logging.WARN if opts['--quiet'] else logging.INFO
    )

    user = opts['--user'] if opts['--user'] is not None else getpass.getuser()
    uid = int(opts['--uid']) if opts['--uid'] is not None else os.getuid()
    logging.info('Will create container for user %s (%s)', user, uid)

    host_ip = socket.gethostbyname(opts['--ip'])
    logging.info('Binding host ports to IP %s', host_ip)

    # Create a new Docker client
    c = docker.Client()

    # Check for a downloaded container image
    imgs = c.images(CONTAINER_IMAGE_REPO)
    if len(imgs) == 0:
        logging.info('Pulling %s...', CONTAINER_IMAGE_REPO)
        c.pull(CONTAINER_IMAGE_REPO)
        imgs = c.images(CONTAINER_IMAGE_REPO)
    if len(imgs) == 0:
        logging.error('No image from repo %s found', CONTAINER_IMAGE_REPO)
        return 1

    img = imgs[0]
    logging.info(
        'Using image %s (%s)', img['Id'][:10], ','.join(img['RepoTags'])
    )

    def ctr_vol_name(v):
        return '/volumes/{}'.format(
            os.path.basename(os.path.abspath(v))
        )

    # Construct bind mounts
    volumes = opts['<volumedir>']
    binds = dict(
        (v, { 'bind': ctr_vol_name(v), 'mode': 'rw' })
        for v in volumes
    )

    # Add .ssh directory as ro mount if present
    ssh_dir = os.path.expanduser('~/.ssh/')
    if os.path.isdir(ssh_dir):
        volumes.append(ssh_dir)
        binds[ssh_dir] = {
            'bind': '/ssh/{}'.format(user),
            'mode': 'ro'
        }
        logging.info('Adding .ssh bind: %s', binds[ssh_dir])

    logging.info('Volumes: %s', ', '.join(volumes))
    logging.info('Binds: %s', ', '.join(
        '{} => {}'.format(k, v) for k, v in binds.items()
    ))

    # Create a container from the image and start it
    ctr = c.create_container(
        image=CONTAINER_IMAGE_REPO, ports=[8888],
        environment={'USER': user, 'USER_UID': uid},
        hostname='{}-compute'.format(user),
        volumes=volumes,
        host_config=c.create_host_config(
            port_bindings={8888: (host_ip,)}, binds=binds,
        ),
    )
    ctr_id = ctr['Id']
    logging.info('Created container %s', ctr['Id'][:10])
    logging.info('Starting...')
    c.start(container=ctr_id)

    # Wait for container
    logging.info('Waiting for start...')
    for l in c.logs(ctr_id, stream=True):
        if 'NotebookApp' in l.decode('utf8', 'replace'):
            break

    # Schedule some exec instances to set up useful links
    if len(volumes) > 0:
        logging.info('Linking bind mounts into notebook dir...')
        e_id = c.exec_create(
            ctr_id, [
                '/bin/bash', '-c',
                '''
                    mkdir -p ~/notebooks/data &&
                    if [ -d "/ssh/${USER}" ]; then
                        ln -s "/ssh/${USER}" ~/.ssh;
                    fi &&
                    for d in /volumes/*; do
                        ln -s "${d}" ~/notebooks/data/"$(basename "${d}")"
                    done
                ''',
            ], user=user
        )
        for l in c.exec_start(e_id).decode('utf8', 'replace').splitlines():
            logging.info('output:%s', l)

    ctr_info = c.inspect_container(ctr_id)
    ctr_name = ctr_info['Name'].lstrip('/')

    # Find port mapping
    port_map = c.port(ctr_id, 8888)
    urls = ['http://{HostIp}:{HostPort}/'.format(**pd) for pd in port_map]

    print('Access container on:')
    for u in urls:
        print(' - ' + u)

    print('Kill *AND DELETE* container using command:')
    print('docker rm -f ' + ctr_name)

    return 0 # SUCCESS


import datetime
import os
import re
import struct


def fill_delegate_proxy_activation_requirements(
    requirements_data, cred_file, lifetime_hours=12
):
    """
    Given the activation requirements for an endpoint and a filename for
    X.509 credentials, extracts the public key from the activation
    requirements, uses the key and the credentials to make a proxy credential,
    and returns the requirements data with the proxy chain filled in.
    """
    # get the public key from the activation requirements
    for data in requirements_data["DATA"]:
        if data["type"] == "delegate_proxy" and data["name"] == "public_key":
            public_key = data["value"]
            break
    else:
        raise ValueError(
            "No public_key found in activation requirements, this endpoint "
            "does not support Delegate Proxy activation."
        )

    # get user credentials from user credential file"
    with open(cred_file) as f:
        issuer_cred = f.read()

    # create the proxy credentials
    proxy = create_proxy_credentials(issuer_cred, public_key, lifetime_hours)

    # return the activation requirements document with the proxy_chain filled
    for data in requirements_data["DATA"]:
        if data["type"] == "delegate_proxy" and data["name"] == "proxy_chain":
            data["value"] = proxy
            return requirements_data
    else:
        raise ValueError(
            "No proxy_chain found in activation requirements, this endpoint "
            "does not support Delegate Proxy activation."
        )


def create_proxy_credentials(issuer_cred, public_key, lifetime_hours):
    """
    Given an issuer credentials PEM file in the form of a string, a public_key
    string from an activation requirements document, and an int for the
    proxy lifetime, returns credentials as a unicode string in PEM format
    containing a new proxy certificate and an extended proxy chain.
    """

    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import serialization

    # parse the issuer credential
    loaded_cert, loaded_private_key, issuer_chain = parse_issuer_cred(issuer_cred)

    # load the public_key into a cryptography object
    loaded_public_key = serialization.load_pem_public_key(
        public_key.encode("ascii"), backend=default_backend()
    )

    # check that the issuer certificate is not an old proxy
    # and is using the keyUsage section as required
    confirm_not_old_proxy(loaded_cert)
    validate_key_usage(loaded_cert)

    # create the proxy cert cryptography object
    new_cert = create_proxy_cert(
        loaded_cert, loaded_private_key, loaded_public_key, lifetime_hours
    )

    # extend the proxy chain as a unicode string
    extended_chain = (
        loaded_cert.public_bytes(serialization.Encoding.PEM).decode("ascii")
        + issuer_chain
    )

    # return in PEM format as a unicode string
    return (
        new_cert.public_bytes(serialization.Encoding.PEM).decode("ascii")
        + extended_chain
    )


def parse_issuer_cred(issuer_cred):
    """
    Given an X509 PEM file in the form of a string, parses it into sections
    by the PEM delimiters of: -----BEGIN <label>----- and -----END <label>----
    Confirms the sections can be decoded in the proxy credential order of:
    issuer cert, issuer private key, proxy chain of 0 or more certs .
    Returns the issuer cert and private key as loaded cryptography objects
    and the proxy chain as a potentially empty string.
    """
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import serialization

    # get each section of the PEM file
    sections = re.findall(
        "-----BEGIN.*?-----.*?-----END.*?-----", issuer_cred, flags=re.DOTALL
    )
    try:
        issuer_cert = sections[0]
        issuer_private_key = sections[1]
        issuer_chain_certs = sections[2:]
    except IndexError:
        raise ValueError(
            "Unable to parse PEM data in credentials, "
            "make sure the X.509 file is in PEM format and "
            "consists of the issuer cert, issuer private key, "
            "and proxy chain (if any) in that order."
        )

    # then validate that each section of data can be decoded as expected
    try:
        loaded_cert = x509.load_pem_x509_certificate(
            issuer_cert.encode("utf-8"), default_backend()
        )
        loaded_private_key = serialization.load_pem_private_key(
            issuer_private_key.encode("utf-8"), password=None, backend=default_backend()
        )
        for chain_cert in issuer_chain_certs:
            x509.load_pem_x509_certificate(
                chain_cert.encode("utf-8"), default_backend()
            )
        issuer_chain = "".join(issuer_chain_certs)
    except ValueError:
        raise ValueError(
            "Failed to decode PEM data in credentials. Make sure "
            "the X.509 file consists of the issuer cert, "
            "issuer private key, and proxy chain (if any) "
            "in that order."
        )

    # return loaded cryptography objects and the issuer chain
    return loaded_cert, loaded_private_key, issuer_chain


def create_proxy_cert(
    loaded_cert, loaded_private_key, loaded_public_key, lifetime_hours
):
    """
    Given cryptography objects for an issuing certificate, a public_key,
    a private_key, and an int for lifetime in hours, creates a proxy
    cert from the issuer and public key signed by the private key.
    """
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes

    builder = x509.CertificateBuilder()

    # create a serial number for the new proxy
    # Under RFC 3820 there are many ways to generate the serial number. However
    # making the number unpredictable has security benefits, e.g. it can make
    # this style of attack more difficult:
    # http://www.win.tue.nl/hashclash/rogue-ca
    serial = struct.unpack("<Q", os.urandom(8))[0]
    builder = builder.serial_number(serial)

    # set the new proxy as valid from now until lifetime_hours have passed
    builder = builder.not_valid_before(datetime.datetime.utcnow())
    builder = builder.not_valid_after(
        datetime.datetime.utcnow() + datetime.timedelta(hours=lifetime_hours)
    )

    # set the public key of the new proxy to the given public key
    builder = builder.public_key(loaded_public_key)

    # set the issuer of the new cert to the subject of the issuing cert
    builder = builder.issuer_name(loaded_cert.subject)

    # set the new proxy's subject
    # append a CommonName to the new proxy's subject
    # with the serial as the value of the CN
    new_atribute = x509.NameAttribute(x509.oid.NameOID.COMMON_NAME, str(serial))
    subject_attributes = list(loaded_cert.subject)
    subject_attributes.append(new_atribute)
    builder = builder.subject_name(x509.Name(subject_attributes))

    # add proxyCertInfo extension to the new proxy (We opt not to add keyUsage)
    # For RFC proxies the effective usage is defined as the intersection
    # of the usage of each cert in the chain. See section 4.2 of RFC 3820.

    # the constants 'oid' and 'value' are gotten from
    # examining output from a call to the open ssl function:
    # X509V3_EXT_conf(NULL, ctx, name, value)
    # ctx set by X509V3_set_nconf(&ctx, NCONF_new(NULL))
    # name = "proxyCertInfo"
    # value = "critical,language:Inherit all"
    oid = x509.ObjectIdentifier("1.3.6.1.5.5.7.1.14")
    value = b"0\x0c0\n\x06\x08+\x06\x01\x05\x05\x07\x15\x01"
    extension = x509.extensions.UnrecognizedExtension(oid, value)
    builder = builder.add_extension(extension, critical=True)

    # sign the new proxy with the issuer's private key
    new_certificate = builder.sign(
        private_key=loaded_private_key,
        algorithm=hashes.SHA256(),
        backend=default_backend(),
    )

    # return the new proxy as a cryptography object
    return new_certificate


def confirm_not_old_proxy(loaded_cert):
    """
    Given a cryptography object for the issuer cert, checks if the cert is
    an "old proxy" and raise an error if so.
    """
    from cryptography import x509

    # Examine the last CommonName to see if it looks like an old proxy.
    last_cn = loaded_cert.subject.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME)[
        -1
    ]
    # if the last CN is 'proxy' or 'limited proxy' we are in an old proxy
    if last_cn.value in ("proxy", "limited proxy"):
        raise ValueError(
            "Proxy certificate is in an outdated format that is no longer supported"
        )


def validate_key_usage(loaded_cert):
    """
    Given a cryptography object for the issuer cert, checks that if
    the keyUsage extension is being used that the digital signature
    bit has been asserted. (As specified in RFC 3820 section 3.1.)
    """
    from cryptography import x509

    try:
        key_usage = loaded_cert.extensions.get_extension_for_oid(
            x509.oid.ExtensionOID.KEY_USAGE
        )
        if not key_usage.value.digital_signature:
            raise ValueError(
                "Certificate is using the keyUsage extension, but has "
                "not asserted the Digital Signature bit."
            )
    except x509.ExtensionNotFound:  # keyUsage extension not used
        return

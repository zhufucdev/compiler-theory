import platform

if platform.machine() == 'x86_64':
    from assemble_x64 import assemble
elif platform.machine() == 'arm64':
    from assemble_arm64 import assemble
else:
    raise NotImplementedError("This platform is not supported")

assemble()

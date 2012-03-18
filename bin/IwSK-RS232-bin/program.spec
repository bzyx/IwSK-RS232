# -*- mode: python -*-
a = Analysis([os.path.join(HOMEPATH,'support\\_mountzlib.py'), os.path.join(HOMEPATH,'support\\useUnicode.py'), 'D:\\Karol\\Project\\IwSK-RS232\\program.py'],
             pathex=['C:\\Users\\Skoruch\\build\\pyinstaller'])
pyz = PYZ(a.pure)
exe = EXE( pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name=os.path.join('dist', 'program.exe'),
          debug=False,
          strip=False,
          upx=True,
          console=True )

# Bytecode evidence excerpts

Base APK SHA-256: `a9a76d5b15f1ed13f0fd368ebbc2cf0bb3c8567d15e4d229944865358d31c5a9`.

Generated with Android SDK apkanalyzer. Names are raw DEX names; JADX may display obfuscated classes under `defpackage`. Each range refers to lines in the complete method disassembly. Excerpts omit surrounding instructions and do not establish runtime execution.

## E04A: Tracker provider setter

Class: `com.my.tracker.MyTrackerConfig`

Method: `setInstalledPackagesProvider(Le5c;)Lcom/my/tracker/MyTrackerConfig;`

Full method disassembly SHA-256: `860c3d419a08d16223c144c8461e3a25a619bee3d62887916db5c1cb9fd73b7d`

Disassembly lines 1–10:

```smali
.method public setInstalledPackagesProvider(Le5c;)Lcom/my/tracker/MyTrackerConfig;
    .registers 2

    iget-object p1, p0, Lcom/my/tracker/MyTrackerConfig;->a:Lcpj;

    invoke-virtual {p1}, Ljava/lang/Object;->getClass()Ljava/lang/Class;

    return-object p0
.end method

```

## E04B: Disk roots and conditional sample scheduling

Class: `ru.ok.tracer.disk.usage.DiskUsageWorker`

Method: `d()Loz9;`

Full method disassembly SHA-256: `5b6ea7066e622fe3580d4b7a900d10ebdcac5bfef4ac19dd54d74a40bdc03567`

Disassembly lines 61–120:

```smali

    invoke-direct {v5}, Ljava/util/LinkedHashMap;-><init>()V

    :try_start_38
    iget-object v6, v2, Landroid/content/pm/ApplicationInfo;->dataDir:Ljava/lang/String;

    sget-object v7, Lga8;->b:Lga8;

    invoke-virtual {p0, v6, v7, v5}, Lru/ok/tracer/disk/usage/DiskUsageWorker;->g(Ljava/lang/String;Lga8;Ljava/util/LinkedHashMap;)V

    const/4 v6, 0x0

    invoke-virtual {v0, v6}, Landroid/content/Context;->getExternalFilesDir(Ljava/lang/String;)Ljava/io/File;

    move-result-object v7

    if-eqz v7, :cond_51

    invoke-virtual {v7}, Ljava/io/File;->getParentFile()Ljava/io/File;

    move-result-object v7

    if-eqz v7, :cond_51

    invoke-virtual {v7}, Ljava/io/File;->getPath()Ljava/lang/String;

    move-result-object v7

    goto :goto_52

    :cond_51
    move-object v7, v6

    :goto_52
    sget-object v8, Lga8;->c:Lga8;

    invoke-virtual {p0, v7, v8, v5}, Lru/ok/tracer/disk/usage/DiskUsageWorker;->g(Ljava/lang/String;Lga8;Ljava/util/LinkedHashMap;)V

    new-instance v7, Ljava/io/File;

    iget-object v2, v2, Landroid/content/pm/ApplicationInfo;->sourceDir:Ljava/lang/String;

    invoke-direct {v7, v2}, Ljava/io/File;-><init>(Ljava/lang/String;)V

    invoke-virtual {v7}, Ljava/io/File;->getParentFile()Ljava/io/File;

    move-result-object v2

    if-eqz v2, :cond_68

    invoke-virtual {v2}, Ljava/io/File;->getPath()Ljava/lang/String;

    move-result-object v6

    :cond_68
    sget-object v2, Lga8;->d:Lga8;

    invoke-virtual {p0, v6, v2, v5}, Lru/ok/tracer/disk/usage/DiskUsageWorker;->g(Ljava/lang/String;Lga8;Ljava/util/LinkedHashMap;)V

    invoke-virtual {v5}, Ljava/util/LinkedHashMap;->values()Ljava/util/Collection;
```

Disassembly lines 156–195:

```smali
    check-cast p0, Lw46;

    invoke-virtual {p0}, Ljava/lang/Object;->getClass()Ljava/lang/Class;

    const-wide v6, 0x280000000L

    cmp-long p0, v3, v6

    if-lez p0, :cond_ba

    invoke-static {v0, v1}, Lf0c;->g(Landroid/content/Context;Lc0c;)Ljava/io/File;

    move-result-object v2

    invoke-static {v5, v3, v4}, Lru/ok/tracer/disk/usage/DiskUsageWorker;->e(Ljava/util/LinkedHashMap;J)Ljava/lang/String;

    move-result-object p0

    invoke-static {v2, p0}, Lef7;->f0(Ljava/io/File;Ljava/lang/String;)V

    invoke-static {v3, v4}, Ljava/lang/Long;->valueOf(J)Ljava/lang/Long;

    move-result-object v4

    const-string p0, "limit"

    invoke-static {v6, v7}, Ljava/lang/String;->valueOf(J)Ljava/lang/String;

    move-result-object v3

    invoke-static {p0, v3}, Ljava/util/Collections;->singletonMap(Ljava/lang/Object;Ljava/lang/Object;)Ljava/util/Map;

    move-result-object v5

    const/16 v6, 0xb8

    const/4 v3, 0x0

    invoke-static/range {v0 .. v6}, Lrug;->q(Landroid/content/Context;Lc0c;Ljava/io/File;Ljava/lang/String;Ljava/lang/Long;Ljava/util/Map;I)V
    :try_end_ba
```

## E04C: Package query

Class: `n16`

Method: `a(Ld55;)Ljava/lang/Object;`

Full method disassembly SHA-256: `8abc80800b8bea7deb73ef1a533c41c1753465371843f1e880e3b10da1f9acf5`

Disassembly lines 64–80:

```smali

    :try_start_34
    iget-object p1, p0, Ln16;->a:Landroid/content/Context;

    invoke-virtual {p1}, Landroid/content/Context;->getPackageManager()Landroid/content/pm/PackageManager;

    move-result-object p1

    const/16 v1, 0x8

    invoke-virtual {p1, v1}, Landroid/content/pm/PackageManager;->getInstalledPackages(I)Ljava/util/List;

    move-result-object p1

    check-cast p1, Ljava/lang/Iterable;

    new-instance v1, Lq00;
```

## E04D: Fixed logcat command

Class: `bi6`

Method: `C(Ljava/lang/Object;)Ljava/lang/Object;`

Full method disassembly SHA-256: `46e2df1924f67546a9749156ad9db7ed7d1ccff8e03ef553e46ac5189d5b3b29`

Disassembly lines 29–51:

```smali
    invoke-virtual {p1, v2}, Ljava/text/DateFormat;->format(Ljava/util/Date;)Ljava/lang/String;

    move-result-object p1

    invoke-static {}, Ljava/lang/Runtime;->getRuntime()Ljava/lang/Runtime;

    move-result-object v2

    const-string v3, "logcat"

    const-string v4, "-v"

    const-string v5, "tag"

    const-string v6, "-T"

    filled-new-array {v3, v4, v5, v6, p1}, [Ljava/lang/String;

    move-result-object p1

    invoke-virtual {v2, p1}, Ljava/lang/Runtime;->exec([Ljava/lang/String;)Ljava/lang/Process;

    move-result-object p1
```

## E04E: JavaScript bridges

Class: `pil`

Method: `d(Ljava/lang/Object;)Ljava/lang/Object;`

Full method disassembly SHA-256: `db79d718b70290739808a3634efb95244ed0482ef7c7e36e215a0b7e01403da6`

Disassembly lines 698–738:

```smali
    invoke-virtual {v6}, Lone/me/webapp/rootscreen/WebAppRootScreen;->N1()Lekl;

    move-result-object v2

    invoke-direct {v0, v2}, Ljql;-><init>(Lekl;)V

    const-string v2, "WebViewHandler"

    invoke-virtual {v13, v0, v2}, Landroid/webkit/WebView;->addJavascriptInterface(Ljava/lang/Object;Ljava/lang/String;)V

    new-instance v0, Lkfl;

    iget-object v2, v6, Lone/me/webapp/rootscreen/WebAppRootScreen;->n:Lpol;

    invoke-direct {v0, v2}, Lkfl;-><init>(Lpol;)V

    const-string v2, "AndroidPerf"

    invoke-virtual {v13, v0, v2}, Landroid/webkit/WebView;->addJavascriptInterface(Ljava/lang/Object;Ljava/lang/String;)V

    invoke-virtual {v6}, Lone/me/webapp/rootscreen/WebAppRootScreen;->N1()Lekl;

    move-result-object v0

    iget-boolean v0, v0, Lekl;->Z:Z

    if-eqz v0, :cond_2f0

    new-instance v0, Lkoe;

    invoke-virtual {v6}, Lone/me/webapp/rootscreen/WebAppRootScreen;->N1()Lekl;

    move-result-object v2

    invoke-direct {v0, v2}, Lkoe;-><init>(Lekl;)V

    const-string v2, "PrivateWebViewHandler"

    invoke-virtual {v13, v0, v2}, Landroid/webkit/WebView;->addJavascriptInterface(Ljava/lang/Object;Ljava/lang/String;)V

    :cond_2f0
```

## E04G: FCM coroutine dispatch

Class: `one.me.sdk.vendor.push.FcmMessagingService`

Method: `d(Lkxf;)V`

Full method disassembly SHA-256: `bb7f420feb6069df7e19e91c9f935fa569caa9a3f2dea860a554d827221b4aa5`

Disassembly lines 271–291:

```smali

    goto :goto_cc

    :goto_f0
    iget-object p0, v3, Loag;->b:Lt45;

    new-instance v1, Lnag;

    const/4 v7, 0x0

    sget-object v4, Lbaf;->d:Lbaf;

    invoke-direct/range {v1 .. v7}, Lnag;-><init>(Ljxf;Loag;Lbaf;JLb55;)V

    const/4 p1, 0x3

    invoke-static {p0, v9, v8, v1, p1}, Lnm9;->J(Lja5;Lx95;ILe18;I)Lg0i;

    return-void
.end method

```

## E04F: Sample upload worker scheduling

Class: `rug`

Method: `q(Landroid/content/Context;Lc0c;Ljava/io/File;Ljava/lang/String;Ljava/lang/Long;Ljava/util/Map;I)V`

Full method disassembly SHA-256: `edd50bd434cc67b022294a3f00d361f160def2667ad4872470e5d5377c180885`

Disassembly lines 234–248:

```smali
    move-wide v13, v11

    invoke-direct/range {v4 .. v15}, Lzu4;-><init>(Lw8c;IZZZZJJLjava/util/Set;)V

    new-instance v1, Landroidx/work/OneTimeWorkRequest$Builder;

    const-class v2, Lru/ok/tracer/upload/SampleUploadWorker;

    invoke-direct {v1, v2}, Lkvl;-><init>(Ljava/lang/Class;)V

    invoke-virtual {v1, v4}, Lkvl;->j(Lzu4;)Lkvl;

    move-result-object v1

    check-cast v1, Landroidx/work/OneTimeWorkRequest$Builder;
```

Disassembly lines 286–302:

```smali
    move-object/from16 p1, v1

    move-object/from16 p0, v2

    move/from16 p3, v3

    move-object/from16 p5, v4

    move-object/from16 p2, v5

    invoke-direct/range {p0 .. p5}, Lgul;-><init>(Lrul;Ljava/lang/String;ILjava/util/List;Ljava/util/List;)V

    move-object/from16 v0, p0

    invoke-virtual {v0}, Lgul;->M()Lgfd;

    return-void
```

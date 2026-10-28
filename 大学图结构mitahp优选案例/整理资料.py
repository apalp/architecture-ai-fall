"""下载已核查的公开资料，保存来源、年份与文件完整性记录；不访问校内认证图纸。"""
import concurrent.futures,hashlib,json,csv
from pathlib import Path
import urllib.request
HERE=Path(__file__).resolve().parent
SOURCES=[
 ('12/12.pdf','https://mitnano.mit.edu/sites/default/files/documents/MITnano_Brochure2024_Final%20Small.pdf','2024','MIT.nano官方手册；不是逐层建筑施工图'),
 ('12/12_建筑性能案例.pdf','https://www.usgbc.org/sites/default/files/2022-03/MIT%20Case%20Study.pdf','2022（文件路径；以正文为准）','USGBC项目案例'),
 ('12/12_室外导览.png','https://mitnano.mit.edu/sites/default/files/2022-11/2022-140%20MIT.nano%20exterior%20points%20of%20interest.png','2022（文件路径）','新MIT.nano周边公共空间导览，不是楼内完整平面'),
 ('12/12_三层局部平面_2021.png','https://mitnano.mit.edu/sites/default/files/inline-images/NanoMat%20Solar%20Frontiers%20construction%20map.png','2021-03-25（发布页）','新MIT.nano三层NanoMat施工范围局部平面；历史局部图，非现状完整平面'),
 ('12/12_官方项目.html','https://capitalprojects.mit.edu/node/32','未标明更新日期','MIT官方项目页'),
 ('12/12_设计方项目.html','https://hga.com/projects/mit-nano/','未标明更新日期','HGA设计方项目页'),
 ('13/13_官方建筑介绍.html','https://listart.mit.edu/art-artists/vannevar-bush-building-1963','未标明更新日期；1963是建筑年份','MIT官方建筑介绍，非完整平面'),
 ('16/16_官方建筑信息.html','https://whereis.mit.edu/?go=16','动态页面，下载日期2026-10-22','MIT校园地图建筑入口，可能需要联网运行'),
 ('26/26_官方建筑信息.html','https://whereis.mit.edu/?go=26','动态页面，下载日期2026-10-22','MIT校园地图建筑入口，可能需要联网运行'),
 ('26/26_研究机构介绍.html','https://www.rle.mit.edu/about/','未标明更新日期','电子学研究实验室官方介绍，明确26号楼为其核心场所之一'),
 ('16/16_跨学科学习空间.html','https://terrascope.mit.edu/academics/','未标明更新日期','Terrascope官方介绍，共享学习活动及16-177地址；不能外推整楼布局'),
 ('12/12_设施楼层说明.html','https://nanousers.mit.edu/index.php/fabnano','未标明更新日期','Fab.nano官方楼层功能说明，非建筑平面'),
 ('13/历史补充/13_10_首层平面来源_2004.pdf','https://ocw.mit.edu/courses/11-947-new-century-cities-real-estate-digital-technology-and-design-fall-2004/c52086015d6dc0e6261b54729328b1fa_mehta_final.pdf','2004-12-01','仅在未取得新版完整平面时留作历史线索；正文页码4，即PDF第5页，含13/10首层平面，不能当现状'),
 ('10/10_105房间平面_2025.pdf','https://sites.mit.edu/institute-events/files/2025/03/Bush-Room-Floor-Plan-Default-Set-Up-2025.pdf','2025（文件名及发布路径）','10-105单个活动房间家具布置，非13号楼，也非10号楼整层平面'),
 ('公共资料/12_13_16_26_楼层连接示意.pdf','https://web.mit.edu/Facilities/maps/mit-accessibility-bw.pdf','2023-11（PDF正文）','全校无障碍地图；第2页含地下与楼层连接，不是房间级平面'),
 ('公共资料/12_13_16_26_图纸访问说明.html','https://libguides.mit.edu/mitbuildings','2025-02-24（页面标示）','官方建筑资料指南；完整平面限MIT社区访问'),
]
def fetch(item):
    filename,url,year,note=item;p=HERE/filename;p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():content=p.read_bytes()
    else:
        request=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(request,timeout=40) as response:content=response.read()
    if p.suffix=='.pdf' and not content.startswith(b'%PDF'):raise ValueError(f'不是PDF：{filename}')
    if p.suffix=='.png' and not content.startswith(b'\x89PNG'):raise ValueError(f'不是PNG：{filename}')
    p.write_bytes(content)
    return {'文件':filename,'来源':url,'资料年份':year,'说明':note,'下载日期':'2026-10-22','字节数':len(content),'SHA256':hashlib.sha256(content).hexdigest(),'状态':'已下载'}
def main():
    records=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures={pool.submit(fetch,item):item for item in SOURCES}
        for future in concurrent.futures.as_completed(futures):
            item=futures[future]
            try:records.append(future.result());print('OK',item[0],flush=True)
            except Exception as e:
                records.append({'文件':item[0],'来源':item[1],'资料年份':item[2],'说明':item[3],'状态':'下载失败','错误':str(e)});print('FAILED',item[0],str(e),flush=True)
    records.sort(key=lambda r:r['文件'])
    (HERE/'来源与下载核验.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    print('downloaded',sum(r['状态']=='已下载' for r in records),'/',len(records))
if __name__=='__main__':main()

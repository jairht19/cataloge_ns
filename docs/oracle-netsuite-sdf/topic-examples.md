# Oracle Topic Examples

## Centers as XML Definitions

Source: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_1516037866.html

```xml
<center scriptid="custcenter_custom">
    <label>My Custom Center</label>
</center>
```

## Center Categories as XML Definitions

Source: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_159542604516.html

```xml
<centercategory scriptid="custcentercategory_custom">
      <center>[scriptid=custcenter_custom]</center>
      <centertab>[scriptid=custcentertab_custom]</centertab>
      <label>My Custom Center Category</label>
      <links>
         <link>
            <linkid>LIST_ACTIVITY</linkid>
            <linklabel>Activity List</linklabel>
            <shortlist>F</shortlist>
         </link>
      </links>
</centercategory>
```

## Center Tabs as XML Definitions

Source: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_1516037901.html

```xml
<centertab scriptid="custcentertab_custom">
    <allroles>T</allroles>
    <center>[scriptid=custcenter_mycenter]</center>
    <label></label>
    <portlets>
        <portlet scriptid="">
            <portlet></portlet>
            <portletcolumn>1</portletcolumn>
            <isportletshown>T</isportletshown>
        </portlet>
    </portlets>
</centertab>
```

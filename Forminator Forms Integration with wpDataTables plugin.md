# Forminator Forms Integration with wpDataTables plugin

## 视频来源

https://www.youtube.com/watch?v=reK3hsYP8Zw

## 大纲

- wpDataTables与Forminator集成介绍 (00:00:04)
    - 欢迎及新集成功能概述 (00:00:04)
        - 兼容性：免费版与完整版均支持 (00:00:14)
        - 演示者介绍：Aleksandar将展示操作流程 (00:00:29)
    - 插件要求与设置 (00:00:44)
        - 下载来源：WordPress.org (00:00:44)
        - 必备插件：wpDataTables、Forminator及集成扩展 (00:03:08)
- 现有表单功能演示 (00:01:09)
    - 活跃模块展示 (00:01:09)
        - 类型：联系表单、消费者投票、常识测验 (00:01:09)
        - 前端显示示例 (00:01:24)
            - 投票可视化：饼图展示 (00:01:43)
            - 测验功能：答案验证与计分 (00:01:55)
            - 联系表单验证：必填字段处理 (00:02:43)
- 从表单数据创建表格 (00:03:38)
    - 联系表单表格创建 (00:03:38)
        - 字段选择流程 (00:03:38)
        - 组合字段的显示格式 (00:04:18)
    - 投票数据表格创建 (00:04:40)
        - 票数统计与显示 (00:05:07)
        - 基于表格数据的图表生成 (00:05:20)
    - 测验结果表格创建 (00:05:56)
        - 颜色编码的答案显示 (00:06:31)
        - 性能指标包含 (00:06:52)
- 高级表格功能 (00:07:00)
    - 筛选选项 (00:07:00)
        - 按条目ID范围筛选 (00:07:03)
        - 基于日期的筛选 (00:07:39)
    - 支持的字段类型 (00:08:33)
        - 包含与排除的表单字段 (00:08:49)
        - 使用钩子的自定义格式化 (00:09:06)
- 前端实现 (00:09:50)
    - 使用Elementor创建页面 (00:09:58)
        - 表格与图表嵌入 (00:10:21)
        - 交互式筛选演示 (00:11:10)
    - 重要限制说明 (00:11:35)
        - 需存在表单提交记录的要求 (00:11:40)
- 总结与行动号召 (00:11:54)
    - 内容回顾 (00:11:54)
    - 互动引导 (00:11:58)
        - 评论区提问
        - 鼓励试用扩展功能
    - 结束语 (00:12:03)
        - 订阅提醒
        - 告别致辞

## 总结

### 一句话总结
- 该视频演示了wpDataTables与Forminator表单的全新集成功能，展示如何在WordPress中通过表单提交数据创建表格和图表。

### 要点
- Forminator表单的wpDataTables集成可免费使用，兼容Forminator专业版和基础版。
- 可从联系表单、测试题、投票等多种Forminator模块创建表格和图表。
- 集成需要三个插件：wpDataTables（轻量版或完整版）、Forminator以及wpDataTables集成扩展。
- 表格可按条目ID、日期范围或最近时段筛选，图表可自定义为饼图或柱状图格式。
- reCAPTCHA验证码、HTML字段、分页区域和GDPR条款等字段不会显示在表格中。

### 深度问答
- 实现wpDataTables与Forminator集成需要哪些插件？
    - 需要wpDataTables（轻量版或完整版）、Forminator以及wpDataTables集成扩展。

- 能否从零提交记录的表单创建表格？
    - 不能，表单至少需要包含一条提交记录才能生成表格。

- 如何筛选表格数据？
    - 可通过条目ID范围、日期范围或最近时段（如过去5天/周/月）进行筛选。

- 投票数据可生成哪些类型的图表？
    - 根据Forminator设置，可生成饼图或柱状图。

- 哪些字段不会出现在表格中？
    - reCAPTCHA验证码、HTML字段、分页区域和GDPR条款等字段会被排除。

### 关键词标签
- wpDataTables
- Forminator
- WordPress
- 数据集成
- 图表与表格

### 目标受众
- WordPress开发者
- 网站管理员
- 数据分析师
- Forminator用户
- wpDataTables用户

### 术语解释
- wpDataTables：用于从多种数据源创建管理表格图表的WordPress插件
- Forminator：用于创建表单/测试/投票的WordPress插件
- 条目ID：每条表单提交记录的唯一标识符，用于筛选追踪
- Highcharts：用于渲染交互式图表的JavaScript库
- reCAPTCHA：防止表单垃圾提交的安全验证功能


![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/8f40c730-2fdb-48e4-b8f2-c4ca22a3cdea.webp)

Speaker1: *00:00:04 - 00:00:14*

大家好，欢迎收看我们的新视频。今天的主题是关于**wpDataTables**与**Forminator Forms**的全新整合功能。

Hello everyone, and welcome to our new video. Today's topic will be our brand new integration between **wpDataTables** and **Forminator Forms**.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/f48aeea3-8a62-4077-aebe-b5b672d61578.webp)

Speaker1: *00:00:14 - 00:00:29*

这是全新推出的集成功能，免费版和完整版均可使用。**Aleksandar**将为我们演示如何基于这些表单创建表格。话不多说，让我们开始吧。

This is the brand new integration that is available in both the free version and our full version. **Aleksandar** will show us how to create forms and tables from those forms. Without further ado, let's dive in.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/7a812bbd-1090-4413-8873-6adee78e042c.webp)

Speaker0: *00:00:29 - 00:00:43*

好的，正如**Bogdan**所说，这个插件是免费的，可以与**Forminator Pro**和**Forminator Basic**（同样也是免费版）一起使用。

Okay, as **Bogdan** mentioned, this add-on is free and it can be used with **Forminator Pro** and **Forminator Basic** (also free version).





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/836a023e-de63-4401-ba00-3b8aca676fb2.webp)

Speaker0: *00:00:44 - 00:00:55*

您可以在**WordPress.org**上下载该插件，其名称为**wpDataTables integration for Forminator Forms**。您可以从这里免费下载——无需支付任何费用。

You can download the add-on on **WordPress.org**. It's named **wpDataTables integration for Forminator Forms**. You can download it from here — you don't need to pay anything.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/328ba40f-f9de-4029-a264-7f6b5bdc2882.webp)

Speaker0: *00:00:56 - 00:01:09*

你可以通过这些表单、**测验**和投票创建几乎任何内容。我们已经创建了一些这样的实例。

You can create basically anything from the forms, from **quizzes**, and from polls. We already have a few of those created.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/b5255fa9-8a99-4db1-81d6-3a191a20a6b2.webp)
![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/c8a3751d-ff59-4027-8946-15dd65381944.webp)
![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/d659c538-8c5c-4c66-95be-6b9efcd49ad5.webp)

Speaker0: *00:01:09 - 00:01:24*

在 **Forminator** 的仪表板中，我们可以看到已有三个活跃模块：联系表单、消费者投票和常识测验。

So in **Forminator**, in the dashboard, we can see that we already have three active modules: the contact form, the consumer poll, and the common sense quiz.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/764b48f9-69f8-4ac9-92ef-2012b6cc0288.webp)

Speaker0: *00:01:24 - 00:01:30*

让我快速展示一下这些在前端的效果。

So let me show you real quick how those look on the front end.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/82180491-5bb4-4364-ba96-856a0aaad49f.webp)

Speaker0: *00:01:31 - 00:01:36*

例如，我们将添加**卡片类型投票**。

We'll just add, for example, **card type poll**.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/8ad75fe2-1371-4d4e-b640-a131d7df5608.webp)

Speaker0: *00:01:38 - 00:01:43*

你拥有什么类型的车？假设是柴油车和两者都有。

What car type do you own? Let's say diesel and both.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/2a8fe14d-4e7b-451a-ac7f-ff3b8b7d7738.webp)

Speaker0: *00:01:43 - 00:01:50*

在这里，你可以直观地看到它在**饼图**上的呈现效果。

And here you can actually see how it looks like on the **pie chart**.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/29193506-0af3-4823-aec8-d860e233790b.webp)

Speaker0: *00:01:51 - 00:01:53*

好的，那么**常识测验**开始。

Okay, so **Common Sense Quiz**.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/ec061953-d912-4caa-8b56-c987d8259f33.webp)

Speaker0: *00:01:55 - 00:02:08*

您需要输入**电子邮箱地址**。例如，我们输入johndoe@com。我同意。提交。然后您就会进入测验。那么迈克尔塔位于何处？

You need to enter the **email address**. For example, let's type in johndoe@com. I agree. Submit. And you're taken to the quiz. So where is Michael Tower located?





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/7bf17246-6ef9-4c02-b90b-f4badc41445c.webp)

Speaker0: *00:02:09 - 00:02:14*

在**巴黎**，如果答案正确，系统会自动显示为绿色。

In **Paris**, it's automatically shown as green if it's the correct answer.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/14a9506a-9bd6-40cd-baf7-e59eabbb7302.webp)

Speaker0: *00:02:14 - 00:02:22*

水的物质状态是什么？假设是**固态**。那么显示为红色，不正确。2加2等于多少？等于4。

What state of matter is water? Let's say **solid**. So it's in red, not correct. What's 2 plus 2? It's 4.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/f9f703cb-cd61-49f6-bffc-c5666b181621.webp)

Speaker0: *00:02:22 - 00:02:29*

篮球是用什么打的？**剑。** 我同意。五道题你答对了三道。

What is basketball played with? **Sword.** I agree. You got three out of five correct.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/d8c8d0aa-2bdb-492e-a886-3ea3586ec103.webp)

Speaker0: *00:02:30 - 00:02:43*

接下来是联系人表单，您需要在此处输入您的姓名，例如 **TMS**。可以看到这是必填项。以**电子邮箱地址**为例。

Next is the contact form where you enter your name, for example, **TMS**. You can see that it's mandatory. Example with the **Email Address**.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/b181f014-cc0a-43ad-9c63-f50bc34917a8.webp)

Speaker0: *00:02:43 - 00:02:57*

如果你点击后又取消选择，它会显示**这是必填字段**。那么我们来输入测试用的邮箱、电话号码和性别。发送消息。

If you click on it and click away, it says **this is a required field**. So let's type in test email, phone number, and gender. Send message.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/eca338f2-57ff-4bad-9e62-d340f02fe0af.webp)

Speaker0: *00:02:59 - 00:03:01*

就这样。好的。还有 **wpDataTables**。

And that's it. Okay. And **wpDataTables**.





Speaker1: *00:03:02 - 00:03:07*

好的。在我们继续之前，能否在**插件**页面展示一下我们需要哪些插件？

Okay. Before we continue, can you show us in the **Plugins** page which plugins we need?





Speaker0: *00:03:08 - 00:03:08*

是的。

Yes.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/6f44d77d-7cee-433b-973c-ca9ad547f9e8.webp)

Speaker0: *00:03:08 - 00:03:37*

在插件页面中，您首先需要的是**wpDataTables**，轻量版或完整版均可。我们这里安装的是完整版，当前版本为3.5。此外还需要配套插件——**Forminator表单的wpDataTables集成扩展**，以及**Forminator插件**本身。

注意：必须同时启用这三个组件，该扩展功能才能正常运行。回到表格创建环节——我们需要新建一个数据表。

In the plugins page, what you need is first **wpDataTables**, light or full version. We have full version installed right here. Current version is 3.5. We need the add-on, so **wpDataTables integration for Forminator Forms**. And we need the **Forminator plugin**. 

Okay, those three need to be enabled in order for this add-on to work. Back to the table - we create a table.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/f992c5ff-5c60-4a0c-a490-51afbcb1df8a.webp)

Speaker0: *00:03:38 - 00:04:17*

我们选择“创建表格”并关联到现有数据源。在此处选择类型为**Forminator表单**。以联系表单为例——选择“联系表单表格”。

勾选需要使用的字段。可跳过“提交日期”、“条目ID”和“用户IP”，这些字段由表单插件自动添加。随后保存更改。

示例如下：  
名：阿尔弗雷德  
名：博格丹  
名：约翰

We select "Create a table" linked to an existing data source. Here, we choose the type, which is **Forminator Form**. We select the Contact Form, for example - Contact Form Table. 

We choose the fields we want to use. We can skip Entry Date, Entry ID, and User IP, as those are added automatically by the forms plugin. Then we save the changes.

Here it is:  
First Name: Alfred  
First Name: Bogdan  
First Name: John





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/f7dddd1f-0526-4db6-9381-3b6d10d095eb.webp)

Speaker0: *00:04:18 - 00:04:23*

如果他们同时输入了**名**和**姓**，这些信息将会像这样显示在同一个单元格中。

If they entered both the **First Name** and the **Last Name**, they will be displayed in a single cell like this.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/8e7dc859-140d-41e0-975f-8cf2702e05bc.webp)

Speaker0: *00:04:24 - 00:04:25*

该单元格将会被展开。

And that cell will be expanded.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/39495fd6-aca3-40b3-8596-8549a8d8c16a.webp)

Speaker0: *00:04:25 - 00:04:29*

所以，我们都有**电子邮箱地址**、**电话号码**和**性别**。

So, we all have the **Email Address**, the **Phone Number**, and **Gender**.





Speaker1: *00:04:30 - 00:04:30*

好的。

Okay.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/e0bf4d0e-11ee-446b-8166-a5a9754e7c72.webp)

Speaker0: *00:04:30 - 00:04:37*

接下来，我们将根据投票结果创建一张表格。

Next, we will create a table from a poll.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/48c79668-4660-40e1-8e7b-8fdcc2f59795.webp)

Speaker1: *00:04:38 - 00:04:38*

好的。

Okay.





Speaker0: *00:04:40 - 00:05:06*

于是，我们再次重复这一流程。**轮询表格**，选择Forminator表单。为饼图选定投票问题——包括投票选项和总票数。保存更改后，效果即刻呈现。

So, we again repeat the process. **Poll table**, and we choose Forminator form. We choose the poll for the pie chart—poll answers and total votes. We save changes, and here it is.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/d534ed39-63c7-4973-8762-730154c70ec8.webp)

Speaker0: *00:05:07 - 00:05:16*

柴油，总票数：9。汽油，总票数：4。以此类推。根据这个表格，我们快速生成一个**图表**吧。

Diesel, total number of votes: 9. Petrol, total number of votes: 4. And so on. From this table, let's create a **chart** real quick.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/fdabd9eb-e86e-498d-804c-6eb7f79c5e4a.webp)

Speaker0: *00:05:20 - 00:05:52*

那么，在**创建图表**下，我们实际上可以添加一个投票图表。首先填写名称，然后选择渲染引擎（这里选择Highcharts）和饼图类型。接着选择投票数据表，点击下一步，再选中这两个字段。这样就能从该表生成饼图了——看，图表已经创建完成了。

现在，让我们用测验数据再创建另一个表格。

So, under **Create a Chart**, we can actually add a poll chart. We have the name. We choose the render engine, which will be Highcharts, and the pie chart. We choose the poll table, click on Next, and then we select these two fields. We can create the pie chart from that table. There it is—the chart is ready.  

Now, let's create another table from the quiz.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/907da35a-b803-4ebb-9e30-f513f488d890.webp)

Speaker0: *00:05:56 - 00:06:13*

那么，再次强调，创建一个链接至现有数据源的表格。**测验表**。我们选择字段。

So, again, create a table linked to an existing data source. **Quiz table**. We select fields.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/c6729ee1-caec-4035-be48-542aee5f3b82.webp)

Speaker1: *00:06:13 - 00:06:19*

因此，这些字段将根据首先选择的表单进行相应更改。

So, those fields will be changed based on which form is selected first.





Speaker0: *00:06:19 - 00:06:31*

当然，是的。这些字段是从表单中提取的。好的。那么，我们**全选这些**，现在你会看到它们已经显示出来了。

Of course, yes. The fields are being pulled from the form. Okay. So, we **select all these** and now you will see that they are displayed.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/38b9fe97-ee63-44db-96fc-b1b08444b74e.webp)

Speaker0: *00:06:31 - 00:06:52*

正确答案显示为**绿色**，错误答案显示为**红色**。您可以查看电子邮件、姓名、测验中的正确答案数量、错误答案数量以及测验结果。如果您不喜欢这些颜色，可以在**Forminator表单**中进行更改。那么，让我们...

Correct answers are in **green**. Incorrect answers are in **red**. You can see the email, the name, how many correct answers were in the quiz, how many incorrect answers were in the quiz, and the results of the quiz. If you don't like these colors, they can be changed in **Forminator Forms**. So, let's...





Speaker1: *00:06:53 - 00:06:53*

好的。

Okay.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/672b2ad2-a1cf-478a-8d15-175697805b29.webp)

Speaker1: *00:06:54 - 00:06:58*

基本上，我可以看到标签页里就有**Forminator设置**。

Basically, I can see that there is **Forminator settings** right there in the tab.





Speaker0: *00:06:58 - 00:06:58*

是的。

Yes.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/b5d3e76c-7d6c-4934-b7df-ecf8926a0f32.webp)

Speaker1: *00:06:58 - 00:07:00*

这是什么意思？

What does that mean?





Speaker0: *00:07:00 - 00:07:03*

您可以按条目ID范围进行筛选。

You can filter by entry ID range.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/8f9a2d7a-43d8-4e14-b764-cf854831f65b.webp)

Speaker0: *00:07:03 - 00:07:13*

那么，根据**条目ID**（就是这里的这个字段），我们可以快速展示一下。

So, based on the **Entry ID**, which is a field right here, we can just show it real quick.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/30d136a5-8d44-4b11-b7ac-ceee860c6f91.webp)

Speaker0: *00:07:13 - 00:07:18*

这是从**Forminator**中获取的条目ID。

This is the ID of the entry taken from **Forminator**.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/af241bbf-b267-46b2-908c-23c1d72cbfbc.webp)

Speaker0: *00:07:18 - 00:07:28*

所以，当你添加那个的时候，它就在这里。这就是它。

So, when you add that, it's here. Here it is.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/7fc29994-123c-4437-9746-540a3590c7d0.webp)

Speaker0: *00:07:28 - 00:07:33*

因此，您可以根据该范围筛选表格。

So, you can filter the table based on that range.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/c8ac7a81-88f1-4134-93e8-6b33b298b88d.webp)

Speaker0: *00:07:33 - 00:07:39*

例如，如果你想显示40到45之间的所有响应，你可以直接在当场进行筛选。

So, for example, if you want to show all responses between 40 and 45, you can just filter it right there on the spot.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/f0b74988-bf1f-42b8-b9ca-caa3522f817a.webp)

Speaker0: *00:07:39 - 00:08:22*

当您**保存更改**后，将仅显示符合条件的条目。您还可按录入日期设置筛选条件，选择日期范围（例如7月1日至7月15日），或按最近时段筛选（如过去5天/周/月/年）。这些选项均存在于表格中，数据源自表单提取。  

（注：技术术语处理说明：  
1. "save the changes" 采用加粗保留原文强调格式  
2. "filter"/"date range" 等专业术语统一译为"筛选条件"/"日期范围"  
3. "pulled from the form" 意译为"数据源自表单提取"以符合中文技术文档表述习惯）

When you **save the changes**, you will see only those entries. You can also set the filter by entry date and choose a date range, such as July 1st until July 15th. Alternatively, you can filter by the last time period, setting it for the past five days, weeks, months, or years. These options are available in the table and are pulled from the form.





Speaker1: *00:08:23 - 00:08:32*

好的，有没有一个列表可以查看我们能在**Forminator**中使用哪些列类型？

Okay, is there any list where we can see which column types we can use with **Forminator**?





Speaker0: *00:08:33 - 00:08:41*

我们可以使用哪些列类型？你可以查看**WordPress.org**上的这份说明。

Which column types can we use? You can take a look at this description on **WordPress.org**.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/2cb9f943-d226-451d-9d29-7e0e22ebaf9a.webp)

Speaker0: *00:08:42 - 00:08:47*

支持的字段列表就在这个项目符号列表中。你可以在那里查看。

The list of supported fields is right here in the bullet list. You can take a look there.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/b0015814-0880-4b26-817b-e4255ff938a3.webp)

Speaker0: *00:08:49 - 00:09:00*

诸如 **reCAPTCHA**、**HTML**、分页符部分以及 **GDPR** 等字段被排除在表格之外，因为你实际上并不需要在表格中使用它们。

The fields like **reCAPTCHA**, **HTML**, page break section, and **GDPR** are excluded from the tables because you don't actually need them for the table.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/cd8bd154-91ac-472c-bb6b-c64419df8f42.webp)

Speaker0: *00:09:00 - 00:09:05*

在这里，你也可以使用钩子。

While we're here, you can also use hooks in here.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/db1eb511-f68e-4129-91ce-f39274154bd7.webp)

Speaker0: *00:09:06 - 00:09:09*

例如，**姓名**和**地址**等字段将被格式化。

For example, fields like **Name** and **Address** will be formatted.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/c7104799-08de-4765-9fcc-60afc1820ea2.webp)

Speaker0: *00:09:10 - 00:09:19*

你可以在插件中使用这些钩子。请继续点击此处查看详情。它们同样适用于**测验**功能。

You can use these hooks in the plugin. Please go ahead and take a look here. They are also available for **quizzes**.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/e69c07a2-1a7b-428f-a8e5-edebae8141bb.webp)

Speaker0: *00:09:20 - 00:09:29*

对于投票，同一份调查的数据可以根据设置以**条形图**或**饼图**的形式展示。

And for polls, the data from the same poll can be displayed in **bar** or **pie chart** depending on the settings.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/d248a646-06df-4da4-8116-11890f69e1ae.webp)

Speaker0: *00:09:30 - 00:09:42*

那么，在**Forminator**仪表板中，我们来看一下——这个投票——如果我们编辑它，你可以在“行为”选项下选择是以饼图还是条形图的形式展示。

So, in the **Forminator** dashboard, let's see—this poll—if we edit it, you can choose under Behavior whether it's going to be displayed in a pie chart or in a bar graph.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/0d1415fa-ddb7-46e8-8442-d98e943562f3.webp)

Speaker0: *00:09:42 - 00:09:48*

不错。

Nice.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/f47e933b-6531-40ae-bb73-8733c76aaa31.webp)

Speaker0: *00:09:50 - 00:09:57*

前端还需要展示哪些内容？比如，可以展示**图表**和**表格**。当然可以。

What's left to show this on the front end? You can show the **chart** and the **table**, for example. Of course.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/1fc514ee-adbe-4384-b530-5f580668d1b8.webp)

Speaker0: *00:09:58 - 00:10:21*

那么，我们来创建一个新页面。将其命名为**Forminator**。发布该页面后，我们将使用Elementor进行编辑。

So, let's create a new page. We'll call it **Forminator**. We'll publish the page and edit it with Elementor.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/e0b5fc16-d057-48bc-a1ce-7faccba92263.webp)

Speaker0: *00:10:21 - 00:10:33*

所以，在这里，你可以输入 **wpDataTables**。

So, in here, you can type in **wpDataTables**.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/572b8f21-b370-4a2f-86d6-04de4c4a699b.webp)

Speaker0: *00:10:33 - 00:10:40*

那么，我们可以把表格加在这里，然后在它下方添加图表。

So, we can add the table right here, and we can add the chart below it.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/dde15a43-5cca-4ce0-aa53-f0660fbd94d0.webp)

Speaker0: *00:10:43 - 00:10:57*

所以，**图表**指的是投票图表，而表格则是投票表格。基本上就是这样。你可以看一下这个页面。这里是表格，下方则是图表。

So, **chart** is the poll chart, and the table will be poll table. That's pretty much it. You can take a look at the page. Here's the table, and here's the chart below.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/de1d8599-d419-421b-8d06-160cef04cfaa.webp)

Speaker0: *00:10:58 - 00:11:06*

好的，目前我们还没有在图表中启用任何筛选功能，但如果我们在这里的**图表**中启用该功能，就能显示不同的数值了。

Okay, now we haven't enabled any filtering in the chart, but we would be able to display different values in the chart if we enable that in the **chart** right here.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/3f46ed93-8e58-42e9-8f72-38e00fd20d64.webp)

Speaker0: *00:11:10 - 00:11:18*

那么，如果我们返回并启用**跟随表格筛选**功能，然后保存图表。

So, if we go back and enable **follow table filtering** and save the chart.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/9020d7d0-78bc-4b1c-aedd-5bfc9b6e5960.webp)

Speaker0: *00:11:21 - 00:11:33*

在这里，当我刷新页面时，如果我输入**Diesel**，就只会显示与Diesel相关的条目。

In here, when I refresh the page, if I type in **Diesel**, only Diesel entries will be shown.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/898cf2f3-4b34-4140-b483-6327c5829b61.webp)

Speaker0: *00:11:34 - 00:11:34*

好的。

Okay.





Speaker1: *00:11:35 - 00:11:40*

顺便提一下，如果表格中没有条目，能否从那里创建一个表格？

Just to mention, if there are no entries in the forms, can you create a table from there?





Speaker0: *00:11:40 - 00:11:40*

编号。

No.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/8ff18e46-a1cf-4f22-9f9e-3f5368a5028e.webp)

Speaker0: *00:11:40 - 00:11:54*

表单中没有任何条目时无法创建表格。您需要至少有一个条目才能基于它创建表格。

好的，谢谢。  
不客气。我想我们已经涵盖所有内容了。

You cannot create a table without any entries in the form. You need to have something, at least one entry in the form, in order to create a table from it. 

Okay, thank you.  
You're welcome. I believe we covered everything.





Speaker1: *00:11:54 - 00:11:58*

如有任何疑问，请在下方评论区告诉我们。

If you have any questions, let us know in the comments section below.





![](https://pic.aihaoji.com/user_7c95832b-eece-61a3-3b56-b32e7f6b3225/img/20250923/b38c812d-bbdf-be76-2249-4ec5868faf3d/d6c93e17-64eb-4345-8699-6e49721632ac.webp)

Speaker1: *00:11:58 - 00:12:03*

另外，请查看我们的新**附加组件**，这样您就可以亲自试用它了。

And also, please check our new **add-on**, so you can try it by yourself.





Speaker0: *00:12:03 - 00:12:09*

好的。谢谢大家。还有一如既往地，别忘了**点赞**、**分享**和**订阅**。

Right. Thanks, guys. And as always, don't forget to **like**, **share**, and **subscribe**.





Speaker1: *00:12:09 - 00:12:11*

下个视频见。保重。再见。

See you in another video. Take care. Bye.






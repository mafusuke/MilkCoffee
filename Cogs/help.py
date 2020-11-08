import asyncio

import discord
from discord.ext import commands

from .utils.multilingual import *


class Help(commands.HelpCommand):
    def __init__(self):
        super().__init__()
        self.no_category = "Help"
        self.command_attrs["description"] = "コマンド一覧を表示します"
        self.command_attrs["help"] = "BOTのヘルプコマンドです"
        self.description_message = ["[分からないことがあれば、公式サーバーまで!]({})", "[Need help? Visit the Support Server!]({})", "[모르는 것이 있으면, 지원용 서버 까지!]({})", "[¿Necesitas ayuda? ¡Visite el servidor de soporte!]({})"]
        self.footer_message = ["{}help (コマンド名) で詳しい説明を表示します", "{}help (command name) to learn more about command", "{}help (명령 이름) 에서 자세한 명령의 설명을 볼 수 있어요!", "m!help (nombre de comando) para obtener más información"]

    async def send_bot_help(self, mapping) -> None:
        """
         引数なしでhelpコマンドが実行された時に表示
        Args:
            mapping: Cogが辞書形式で含まれるデータ

        Returns:
            None
        """
        if str(self.context.author.id) not in self.context.bot.database:
            await self.new_user()
        user_lang = get_lg(self.context.bot.database[str(self.context.author.id)]["language"], self.context.guild.region)
        cogs: list
        page = 1
        cogs = ["Costume", "Notify", "Bot"]
        # 一枚目の全コマンドリストEmbedを作成
        embed_org = discord.Embed(title=f"{self.context.bot.user.name}", color=0x9f563a)
        embed_org.description = self.footer_message[user_lang].format(self.context.bot.PREFIX) + "\n" + self.description_message[user_lang].format(self.context.bot.static_data.server)
        for cog_name in cogs:
            cog = discord.utils.get(mapping, qualified_name=cog_name)
            command_list = [command.name for command in self.filter_hidden_commands(cog.get_commands())]
            embed_org.add_field(name=cog_name, value="`" + "`, `".join(command_list) + "`", inline=False)
        message = await self.get_destination().send(embed=embed_org)
        await message.add_reaction(self.context.bot.data.emoji.left)
        await message.add_reaction(self.context.bot.data.emoji.right)
        await message.add_reaction(self.context.bot.data.emoji.help)

        while True:
            try:
                reaction, user = await self.context.bot.wait_for("reaction_add", timeout=60, check=lambda r, u: r.message.id == message.id and u == self.context.author and str(r.emoji) in [self.context.bot.data.emoji.left, self.context.bot.data.emoji.right, self.context.bot.data.emoji.help])
                try:
                    await message.remove_reaction(reaction, user)
                except:
                    pass
                if str(reaction.emoji) == self.context.bot.data.emoji.right:  # 次のページに進む
                    if page == len(cogs) + 1:
                        page = 1
                    else:
                        page += 1
                elif str(reaction.emoji) == self.context.bot.data.emoji.left:  # 前のページに戻る
                    if page == 1:
                        page = len(cogs) + 1
                    else:
                        page -= 1
                elif str(reaction.emoji) == self.context.bot.data.emoji.help:  # 記号説明ページ
                    embed = discord.Embed(title=self.context.bot.text.help_how_title[user_lang], color=0x9f563a)
                    embed.description = self.footer_message[user_lang].format(self.context.bot.PREFIX) + "\n" + self.description_message[user_lang].format(self.context.bot.static_data.server) + "\n"
                    embed.description += self.context.bot.text.help_main[user_lang]
                    await message.edit(embed=embed)
                    continue
                if page == 1:  # 既に用意された1枚目を表示
                    await message.edit(embed=embed_org)
                    continue
                cog = discord.utils.get(mapping, qualified_name=cogs[page - 2])
                embed = discord.Embed(title=cog.qualified_name, color=0x9f563a)
                desc = cog.description.split("^")[user_lang] + "\n" + self.description_message[user_lang].format(self.context.bot.static_data.server) + "\n"
                command_list = cog.get_commands()
                max_length = self.get_command_max_length(command_list)
                for cmd in self.filter_hidden_commands(command_list):
                    # 適切な空白数分、空白を追加
                    desc += f"\n`{self.context.bot.PREFIX}{cmd.name}" + " " * self.get_space_count(len(cmd.name), max_length) + f"|` {cmd.brief.split('^')[user_lang]}"
                embed.description = desc
                embed.set_footer(text=self.footer_message[user_lang].format(self.context.bot.PREFIX))
                await message.edit(embed=embed)
            except asyncio.TimeoutError:
                await message.clear_reactions()
                break

    def get_space_count(self, name: int, max_length: int) -> int:
        diff = max_length - name
        if diff < 0:
            return 0
        else:
            return diff

    def get_command_max_length(self, command_list):
        max_length = 6
        for command in command_list:
            if len(command.name) > max_length:
                max_length = len(command.name)
        return max_length

    async def send_cog_help(self, cog) -> None:
        """
        コグの説明を表示
        Args:
            cog: Cog

        Returns:
            None
        """
        if str(self.context.author.id) not in self.context.bot.database:
            await self.new_user()
        user_lang = get_lg(self.context.bot.database[str(self.context.author.id)]["language"], self.context.guild.region)
        embed = discord.Embed(title=cog.qualified_name, color=0x9f563a)
        desc = cog.description.split('^')[user_lang] + "\n" + self.description_message[user_lang].format(self.context.bot.static_data.server) + "\n"
        command_list = cog.get_commands()
        max_length = self.get_command_max_length(command_list)
        for cmd in self.filter_hidden_commands(command_list):
            desc += f"\n`{self.context.bot.PREFIX}{cmd.name}" + " " * self.get_space_count(len(cmd.name), max_length) + f"|` {cmd.brief.split('^')[user_lang]}"
        embed.description = desc
        embed.set_footer(text=self.footer_message[user_lang].format(self.context.bot.PREFIX))
        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group):
        """
        コマンドグループの説明を表示
        Args:
            group: group

        Returns:
            None
        """
        if str(self.context.author.id) not in self.context.bot.database:
            await self.new_user()
        user_lang = get_lg(self.context.bot.database[str(self.context.author.id)]["language"], self.context.guild.region)
        embed = discord.Embed(title=f"{self.context.bot.PREFIX}{group.usage.split('^')[user_lang]}", color=0x9f563a)
        desc = f"{group.description.split('^')[user_lang]}\n\n"
        if group.aliases:
            embed.add_field(name="Aliases:", value="`" + "`, `".join(group.aliases) + "`", inline=False)
        if group.help:
            embed.add_field(name="Example:", value=group.help.format(self.context.bot.PREFIX), inline=False)
        cmds = group.walk_commands()
        for cmd in self.filter_hidden_commands(cmds, sort=True):
            desc += f"**{self.context.bot.PREFIX}{cmd.usage.split('^')[user_lang]}**\n-> *{cmd.description.split('^')[user_lang]}*\n\n"
        embed.description = desc
        embed.set_footer(text=self.footer_message[user_lang].format(self.context.bot.PREFIX))
        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command) -> None:
        """
        コマンドの説明を表示
        Args:
            command: Command

        Returns:
            None
        """
        if str(self.context.author.id) not in self.context.bot.database:
            await self.new_user()
        user_lang = get_lg(self.context.bot.database[str(self.context.author.id)]["language"], self.context.guild.region)
        embed = discord.Embed(title=f"{self.context.bot.PREFIX}{command.usage.split('^')[user_lang]}", color=0x9f563a)
        embed.description = f"{command.description.split('^')[user_lang]}"
        if command.aliases:
            embed.add_field(name="Aliases:", value="`" + "`, `".join(command.aliases) + "`", inline=False)
        if command.help and "^" in command.help:
            embed.add_field(name="Example:", value=command.help.split('^')[user_lang].format(self.context.bot.PREFIX), inline=False)
        await self.get_destination().send(embed=embed)

    async def send_error_message(self, error) -> None:
        """
        コマンドが存在しないときに表示
        Args:
            error:

        Returns:
            None
        """
        if str(self.context.author.id) not in self.context.bot.database:
            await self.new_user()
        user_lang = get_lg(self.context.bot.database[str(self.context.author.id)]["language"], self.context.guild.region)
        embed = discord.Embed(title=["ヘルプ表示のエラー", "Error displaying help", "도움말 표시 오류", "Ayuda mostrando error"][user_lang], description=error, color=0xff0000)
        embed.set_footer(text=self.footer_message[user_lang].format(self.context.bot.PREFIX))
        await self.get_destination().send(embed=embed)

    def command_not_found(self, string):
        user_lang = get_lg(self.context.bot.database[str(self.context.author.id)]["language"], self.context.guild.region)
        return ["`{}` というコマンドは見つかりませんでした。コマンド名を再確認してください", "Couldn't find the command `{}`. Double check the command name!", "`{}`명령을 찾을 수 없습니다. 명령 이름을 다시 확인하십시오!", "No pude encontrar el comando {}. ¡Verifique el nombre del comando!"][user_lang].format(string)

    def subcommand_not_found(self, cmd, string):
        user_lang = get_lg(self.context.bot.database[str(self.context.author.id)]["language"], self.context.guild.region)
        if isinstance(cmd, commands.Group) and len(cmd.all_commands) > 0:
            return ["`{1}` に `{0}` というサブコマンドは存在しません。`{2}help {1}` で使い方を確認できます", "The subcommand `{0}` is not registered in `{1}`. Please check the usage with `{2}help {1}`!", "하위 명령어`{0}`이 (가)`{1}`에 등록되지 않았습니다. `{2}help {1}`로 사용법을 확인하세요!", "El subcomando `{0}` no está registrado en `{1}`. ¡Compruebe el uso con la `{2}help {1}`!"][user_lang].format(string, cmd.qualified_name,
                                                                                                                                                                                                                                                                                                                                                                 self.context.bot.PREFIX)
        return ["`{0}` にサブコマンドは存在しません。`{1}help {0}` で使い方を確認できます", "No subcommands are registered in `{0}`. Please check the usage with `{1}help {0}`!", "`{0}`에 등록 된 하위 명령이 없습니다.`{1}help {0}`로 사용법을 확인하세요!", "No hay subcomandos registrados en `{0}`.¡Compruebe el uso con la `{1}help {0}`!"][user_lang].format(cmd.qualified_name, self.context.bot.PREFIX)

    async def new_user(self):
        if str(self.context.author.id) not in self.context.bot.database:
            self.context.bot.database[str(self.context.author.id)] = {
                "language": 0,
                "costume": {
                    "canvas": "1o4s3k",
                    "save": []
                }
            }
            await self.context.bot.get_cog("Bot").language_selector(self.context)

    def filter_hidden_commands(self, command_list, sort=False):
        """コマンドリストの中から隠し属性を持つコマンドを削除"""
        res = [cmd for cmd in command_list if not cmd.hidden]
        if sort:
            res.sort(key=lambda cmd: cmd.qualified_name)
        return res

from grbl.parsers.grblParserGeneric import GrblParserGeneric
from grbl.parsers.grblParserMsgAlarm import GrblParserMsgAlarm
from grbl.parsers.grblParserMsgEcho import GrblParserMsgEcho
from grbl.parsers.grblParserMsgFeedback import GrblParserMsgFeedback
from grbl.parsers.grblParserMsgHelp import GrblParserMsgHelp
from grbl.parsers.grblParserMsgOptions import GrblParserMsgOptions
from grbl.parsers.grblParserMsgParameters import GrblParserMsgParameters
from grbl.parsers.grblParserMsgParserState import GrblParserMsgParserState
from grbl.parsers.grblParserMsgSettings import GrblParserMsgSettings
from grbl.parsers.grblParserMsgStartup import GrblParserMsgStartup
from grbl.parsers.grblParserMsgStatus import GrblParserMsgStatus
from grbl.parsers.grblParserMsgUserDefinedStartup import GrblParserMsgUserDefinedStartup
from grbl.parsers.grblParserMsgVersion import GrblParserMsgVersion
from grbl.parsers.grblParserResultError import GrblParserResultError
from grbl.parsers.grblParserResultOk import GrblParserResultOk

class GrblLineParser:
    @staticmethod
    def parse(line: str) -> tuple[str | None, dict[str, str]]:
        parsers: list[GrblParserGeneric] = [
            # * Grbl v1.1
            #   <Idle|MPos:3.000,2.000,0.000|FS:0,0>
            #   <Hold:0|MPos:5.000,2.000,0.000|FS:0,0>
            #   <Idle|MPos:5.000,2.000,0.000|FS:0,0|Ov:100,100,100>
            #   <Idle|MPos:5.000,2.000,0.000|FS:0,0|WCO:0.000,0.000,0.000>
            #   <Run|MPos:23.036,1.620,0.000|FS:500,0>
            GrblParserMsgStatus,

            # ok
            GrblParserResultOk,

            # error:x
            GrblParserResultError,

            # ALARM:
            GrblParserMsgAlarm,

            # [G38.2 G54 G17 G21 G91 G94 M0 M5 M9 T0 F20. S0.] (v0.9)
            # [GC:G38.2 G54 G17 G21 G91 G94 M0 M5 M9 T0 F20. S0.] (v1.1)
            GrblParserMsgParserState,

            # [G54:0.000,0.000,0.000]
            # [G55:0.000,0.000,0.000]
            # [G56:0.000,0.000,0.000]
            # [G57:0.000,0.000,0.000]
            # [G58:0.000,0.000,0.000]
            # [G59:0.000,0.000,0.000]
            # [G28:0.000,0.000,0.000]
            # [G30:0.000,0.000,0.000]
            # [G92:0.000,0.000,0.000]
            # [TLO:0.000]
            # [PRB:0.000,0.000,0.000:0]
            GrblParserMsgParameters,

            # [HLP:] (v1.1)
            GrblParserMsgHelp,

            # [VER:] (v1.1)
            GrblParserMsgVersion,

            # [OPT:] (v1.1)
            GrblParserMsgOptions,

            # [echo:] (v1.1)
            GrblParserMsgEcho,

            # [] (v0.9)
            # [MSG:] (v1.1)
            GrblParserMsgFeedback,

            # $N=line
            GrblParserMsgUserDefinedStartup,

            # $x=val
            GrblParserMsgSettings,

            # Grbl X.Xx ['$' for help]
            GrblParserMsgStartup
        ]

        for parser in parsers:
            result = parser.parse(line)
            if result:
                # Add a "rawline" field to the payload dictionary
                result[1].update({'raw': line})
                return result

        return None, { 'raw': line }

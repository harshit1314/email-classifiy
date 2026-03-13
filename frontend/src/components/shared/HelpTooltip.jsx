import React from 'react'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Info } from 'lucide-react'

const HelpTooltip = ({ title, description, children }) => {
    return (
        <Popover>
            <PopoverTrigger asChild>
                <button className="inline-flex items-center justify-center rounded-full hover:bg-gray-100 p-0.5 transition-colors">
                    {children || <Info className="w-4 h-4 text-gray-400" />}
                </button>
            </PopoverTrigger>
            <PopoverContent className="w-80 p-4">
                <div className="space-y-2">
                    <h4 className="font-semibold text-sm flex items-center gap-2">
                        <Info className="w-4 h-4 text-blue-500" />
                        {title}
                    </h4>
                    <p className="text-xs text-gray-600 leading-relaxed">
                        {description}
                    </p>
                </div>
            </PopoverContent>
        </Popover>
    )
}

export default HelpTooltip
